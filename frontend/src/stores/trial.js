import{list}from'../api/trial.js';export const trials={items:[],async load(){this.items=await list();return this.items}};
