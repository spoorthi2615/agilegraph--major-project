import { useRef, useEffect, useState, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import type { GraphResponse } from '../api/client';

interface GraphViewProps {
  data: GraphResponse;
  selectedAssetId: string | null;
  onNodeClick: (nodeId: string) => void;
}

export default function GraphView({ data, selectedAssetId, onNodeClick }: GraphViewProps) {
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

  // Format data for react-force-graph memoized to prevent physics re-simulation on every render
  const graphData = useMemo(() => ({
    nodes: (data?.nodes || []).map(n => ({ id: n.id, name: n.id, val: 1.5, category: n.category || 'file' })),
    links: (data?.edges || []).map(e => ({ source: e.source, target: e.target }))
  }), [data]);

  const getNodeColor = (node: any) => {
    if (selectedAssetId && node.id !== selectedAssetId) {
      return '#334155'; // dimmed if not selected
    }
    switch(node.category) {
      case 'file': return selectedAssetId === node.id ? '#93c5fd' : '#60a5fa'; // blue
      case 'library': return selectedAssetId === node.id ? '#6ee7b7' : '#34d399'; // emerald
      case 'crypto_usage': return selectedAssetId === node.id ? '#d8b4fe' : '#c084fc'; // purple
      default: return '#94a3b8'; // slate
    }
  };
  
  useEffect(() => {
    if (selectedAssetId && fgRef.current) {
      const node = graphData.nodes.find((n: any) => n.id === selectedAssetId) as any;
      if (node && node.x !== undefined && node.y !== undefined) {
        fgRef.current.centerAt(node.x, node.y, 800);
        fgRef.current.zoom(3, 800);
      }
    }
  }, [selectedAssetId, graphData]);

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
        onNodeClick={(node: any) => onNodeClick(node.id)}
      />
    </div>
  );
}
