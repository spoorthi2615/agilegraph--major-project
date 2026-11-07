import { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

interface ProjectContextType {
  projectId: string;
  setProjectId: (id: string) => void;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [projectId, setProjectIdState] = useState<string>(() => {
    try {
      return localStorage.getItem('agilegraph_project_id') || '';
    } catch {
      return '';
    }
  });

  const setProjectId = (id: string) => {
    setProjectIdState(id);
    try {
      if (id) {
        localStorage.setItem('agilegraph_project_id', id);
      } else {
        localStorage.removeItem('agilegraph_project_id');
      }
    } catch {}
  };

  return (
    <ProjectContext.Provider value={{ projectId, setProjectId }}>
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
}
