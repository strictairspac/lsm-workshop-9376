import{list}from'../api/config.js';export const configs={items:[],async load(){this.items=await list();return this.items}};
