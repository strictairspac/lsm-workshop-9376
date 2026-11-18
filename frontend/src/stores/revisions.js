import{list}from'../api/revisions.js';export const revisions={items:[],async load(){this.items=await list();return this.items}};
