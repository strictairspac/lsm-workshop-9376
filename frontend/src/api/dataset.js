import{api,post}from'./client.js';export const list=()=>api('/datasets');export const create=data=>post('/datasets',data);
