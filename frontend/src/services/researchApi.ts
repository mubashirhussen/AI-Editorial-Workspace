import { projectService } from './projectService';
import { researchService } from './researchService';

export const researchApi = {
  ...projectService,
  ...researchService,
};

export { projectService, researchService };
