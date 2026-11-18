import{api,post}from'./client.js';export const list=()=>api('/configs');export const create=data=>post('/configs',data);
