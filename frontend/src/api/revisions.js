import{api,post}from'./client.js';
export const list=()=>api('/revisions');
export const create=data=>post('/revisions',data);
export const detail=id=>api('/revisions/'+id);
export const publish=(id,data)=>post('/revisions/'+id+'/publish',data);
