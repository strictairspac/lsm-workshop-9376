import{api,post}from'./client.js';
export const list=()=>api('/settlements');
export const create=data=>post('/settlements',data);
export const detail=id=>api('/settlements/'+id);
