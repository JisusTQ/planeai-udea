const KEY_ACTUAL = "planeai:chat-actual";
const KEY_HISTORIAL = "planeai:chat-historial";
const MAX_HISTORIAL = 20;

function leer(clave, porDefecto) {
  try {
    const valor = localStorage.getItem(clave);
    return valor ? JSON.parse(valor) : porDefecto;
  } catch {
    return porDefecto;
  }
}

function escribir(clave, valor) {
  try {
    localStorage.setItem(clave, JSON.stringify(valor));
  } catch {
    /* almacenamiento lleno o no disponible: se ignora */
  }
}

export const cargarActual = () => leer(KEY_ACTUAL, null);
export const guardarActual = (mensajes) => escribir(KEY_ACTUAL, mensajes);

export const cargarHistorial = () => leer(KEY_HISTORIAL, []);
export const guardarHistorial = (lista) =>
  escribir(KEY_HISTORIAL, lista.slice(0, MAX_HISTORIAL));
