import{list}from'../api/dataset.js';export const datasets={items:[],async load(){this.items=await list();return this.items}};
