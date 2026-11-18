import{esc}from'../../utils/html.js';
export const badge=(map,s)=>'<span class="badge '+esc(s)+'">'+esc(map[s]||s)+'</span>';
