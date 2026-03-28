"use client";

import { useEffect, useRef } from "react";
import { useChimeraStore } from "@/lib/store";

interface CanvasNode {
  id: string;
  type: string;
  x: number;
  y: number;
  active: boolean;
  rippleTime: number;
}

interface CanvasEdge {
  source: string;
  target: string;
  weight: number;
}

export function RippleGraph() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { graph, rippleActiveNodes } = useChimeraStore();
  const nodesRef = useRef<CanvasNode[]>([]);
  const edgesRef = useRef<CanvasEdge[]>([]);
  const animRef = useRef<number>(0);

  useEffect(() => {
    if (!graph.nodes.length) return;
    const cx = 250;
    const cy = 200;
    const radius = 150;
    nodesRef.current = graph.nodes.map((n, i) => ({
      id: n.id,
      type: n.type || "concept",
      x: cx + radius * Math.cos((2 * Math.PI * i) / graph.nodes.length),
      y: cy + radius * Math.sin((2 * Math.PI * i) / graph.nodes.length),
      active: rippleActiveNodes.has(n.id),
      rippleTime: rippleActiveNodes.has(n.id) ? Date.now() : 0,
    }));
    edgesRef.current = graph.edges.map((e) => ({
      source: e.source,
      target: e.target,
      weight: e.weight,
    }));
  }, [graph]);

  useEffect(() => {
    nodesRef.current.forEach((n) => {
      if (rippleActiveNodes.has(n.id) && !n.active) {
        n.active = true;
        n.rippleTime = Date.now();
      }
    });
  }, [rippleActiveNodes]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const nodes = nodesRef.current;
      const edges = edgesRef.current;
      const nodeMap = new Map(nodes.map((n) => [n.id, n]));

      // Edges
      edges.forEach((e) => {
        const src = nodeMap.get(e.source);
        const tgt = nodeMap.get(e.target);
        if (!src || !tgt) return;

        const active = src.active && tgt.active;
        ctx.strokeStyle = active
          ? "rgba(255,255,255,0.45)"
          : "rgba(255,255,255,0.06)";
        ctx.lineWidth = active ? 1 : 0.5;
        ctx.setLineDash(active ? [3, 5] : []);
        if (active) {
          ctx.lineDashOffset = -(Date.now() / 600) * 8;
        }
        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.lineDashOffset = 0;
      });

      // Nodes
      nodes.forEach((node) => {
        // Ripple rings — white, thin
        if (node.active && node.rippleTime > 0) {
          const elapsed = (Date.now() - node.rippleTime) / 1000;
          if (elapsed < 3) {
            const rippleR = (node.active ? 8 : 5) + elapsed * 22;
            const alpha = Math.max(0, 0.35 - elapsed * 0.12);
            ctx.strokeStyle = `rgba(255,255,255,${alpha.toFixed(2)})`;
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            ctx.arc(node.x, node.y, rippleR, 0, Math.PI * 2);
            ctx.stroke();
          }
        }

        // Node circle
        const r = node.active ? 7 : 4;
        ctx.fillStyle = node.active ? "#ffffff" : "#252525";
        ctx.beginPath();
        ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
        ctx.fill();

        // Label
        ctx.fillStyle = node.active ? "rgba(255,255,255,0.8)" : "rgba(255,255,255,0.2)";
        ctx.font = `${node.active ? 500 : 400} 9px Inter, sans-serif`;
        ctx.textAlign = "center";
        ctx.letterSpacing = "0.05em";
        ctx.fillText(node.id.toUpperCase(), node.x, node.y + r + 11);
      });

      animRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [graph]);

  return (
    <div className="panel" style={{ position: "relative" }}>
      <div className="panel-header">
        <div className="status-dot" style={{ background: "var(--text-2)" }} />
        <span className="label">Ripple Graph</span>
        <span className="label" style={{ marginLeft: "auto" }}>
          {graph.nodes.length} nodes
        </span>
      </div>
      <canvas
        ref={canvasRef}
        width={500}
        height={400}
        style={{ width: "100%", flex: 1, display: "block", minHeight: 0 }}
      />
    </div>
  );
}
