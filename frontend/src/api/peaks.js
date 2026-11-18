import{api}from'./client.js';
export const published=()=>api('/peaks/published');
export const pending=()=>api('/peaks/pending');
export const overview=()=>api('/peaks/overview');
