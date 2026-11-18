import{list}from'../api/settlements.js';export const settlements={items:[],async load(){this.items=await list();return this.items}};
