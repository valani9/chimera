"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useChimeraStore } from "@/lib/store";

const NODE_COLORS: Record<string, string> = {
  country: "#3b82f6",
  person: "#f59e0b",
  organization: "#a855f7",
  concept: "#22c55e",
  event: "#ef4444",
};

interface CanvasNode {
  id: string;
  type: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  active: boolean;
  rippleTime: number;
}

interface CanvasEdge {
  source: string;
  target: string;
  relation: string;
  weight: number;
}

export function RippleGraph() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { graph, rippleActiveNodes } = useChimeraStore();
  const nodesRef = useRef<CanvasNode[]>([]);
  const edgesRef = useRef<CanvasEdge[]>([]);
  const animRef = useRef<number>(0);

  // Initialize nodes with positions
  useEffect(() => {
    if (!graph.nodes.length) return;

    const cx = 250;
    const cy = 200;
    const radius = 140;

    nodesRef.current = graph.nodes.map((n, i) => ({
      id: n.id,
      type: n.type || "concept",
      x: cx + radius * Math.cos((2 * Math.PI * i) / graph.nodes.length),
      y: cy + radius * Math.sin((2 * Math.PI * i) / graph.nodes.length),
      vx: 0,
      vy: 0,
      active: rippleActiveNodes.has(n.id),
      rippleTime: rippleActiveNodes.has(n.id) ? Date.now() : 0,
    }));

    edgesRef.current = graph.edges.map((e) => ({
      source: e.source,
      target: e.target,
      relation: e.relation,
      weight: e.weight,
    }));
  }, [graph]);

  // Update active states
  useEffect(() => {
    nodesRef.current.forEach((n) => {
      if (rippleActiveNodes.has(n.id) && !n.active) {
        n.active = true;
        n.rippleTime = Date.now();
      }
    });
  }, [rippleActiveNodes]);

  // Animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const draw = () => {
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      const nodes = nodesRef.current;
      const edges = edgesRef.current;
      const nodeMap = new Map(nodes.map((n) => [n.id, n]));

      // Draw edges
      edges.forEach((e) => {
        const src = nodeMap.get(e.source);
        const tgt = nodeMap.get(e.target);
        if (!src || !tgt) return;

        const bothActive = src.active && tgt.active;
        ctx.strokeStyle = bothActive ? "#06b6d480" : "#1e1e2e80";
        ctx.lineWidth = bothActive ? 1.5 : 0.5;

        // Animated dashed line for active edges
        if (bothActive) {
          ctx.setLineDash([4, 4]);
          const time = Date.now() / 500;
          ctx.lineDashOffset = -time * 10;
        } else {
          ctx.setLineDash([]);
        }

        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.stroke();
        ctx.setLineDash([]);

        // Arrow head for active edges
        if (bothActive) {
          const angle = Math.atan2(tgt.y - src.y, tgt.x - src.x);
          const headLen = 8;
          const mx = (src.x + tgt.x) / 2;
          const my = (src.y + tgt.y) / 2;
          ctx.fillStyle = "#06b6d480";
          ctx.beginPath();
          ctx.moveTo(mx + headLen * Math.cos(angle), my + headLen * Math.sin(angle));
          ctx.lineTo(mx + headLen * Math.cos(angle + 2.5), my + headLen * Math.sin(angle + 2.5));
          ctx.lineTo(mx + headLen * Math.cos(angle - 2.5), my + headLen * Math.sin(angle - 2.5));
          ctx.fill();
        }
      });

      // Draw nodes
      nodes.forEach((node) => {
        const color = NODE_COLORS[node.type] || "#71717a";
        const r = node.active ? 10 : 6;

        // Ripple ring animation
        if (node.active && node.rippleTime > 0) {
          const elapsed = (Date.now() - node.rippleTime) / 1000;
          if (elapsed < 3) {
            const rippleR = r + elapsed * 20;
            const alpha = Math.max(0, 0.4 - elapsed * 0.13);
            ctx.strokeStyle = `${color}${Math.round(alpha * 255).toString(16).padStart(2, "0")}`;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(node.x, node.y, rippleR, 0, Math.PI * 2);
            ctx.stroke();
          }
        }

        // Glow for active nodes
        if (node.active) {
          ctx.shadowColor = color;
          ctx.shadowBlur = 15;
        }

        // Node circle
        ctx.fillStyle = node.active ? color : `${color}60`;
        ctx.beginPath();
        ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;

        // Label
        ctx.fillStyle = node.active ? "#e4e4e7" : "#71717a";
        ctx.font = `${node.active ? "11px" : "9px"} Inter, sans-serif`;
        ctx.textAlign = "center";
        ctx.fillText(node.id, node.x, node.y + r + 12);
      });

      animRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [graph]);

  return (
    <div className="glass-panel p-3 flex flex-col h-full">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: "#22c55e" }} />
        <span className="text-xs font-semibold text-green-400 mono">RIPPLE KNOWLEDGE GRAPH</span>
      </div>
      <canvas
        ref={canvasRef}
        width={500}
        height={400}
        className="w-full flex-1"
        style={{ minHeight: 0 }}
      />
    </div>
  );
}
