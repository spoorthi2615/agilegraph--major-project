import { useRef, useEffect, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import type { GraphResponse } from '../api/client';

export default function GraphView({ data }: { data: GraphResponse }) {
  const fgRef = useRef<any>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight
      });
    }
    
    const handleResize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        });
      }
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Format data for react-force-graph
  const graphData = {
    nodes: data.nodes.map(n => ({ id: n.id, name: n.id, val: 1.5, category: n.category || 'file' })),
    links: data.edges.map(e => ({ source: e.source, target: e.target }))
  };

  const getNodeColor = (node: any) => {
    switch(node.category) {
      case 'file': return '#60a5fa'; // blue-400
      case 'library': return '#34d399'; // emerald-400
      case 'crypto_usage': return '#c084fc'; // purple-400
      default: return '#94a3b8'; // slate-400
    }
  };

  return (
    <div ref={containerRef} className="w-full h-full absolute inset-0 overflow-hidden">
      <ForceGraph2D
        ref={fgRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeColor={getNodeColor}
        nodeLabel="name"
        nodeRelSize={6}
        linkColor={() => '#334155'}
        linkWidth={1.5}
        backgroundColor="#020617" // slate-950
        cooldownTicks={100}
        onEngineStop={() => fgRef.current?.zoomToFit(400)}
      />
    </div>
  );
}
