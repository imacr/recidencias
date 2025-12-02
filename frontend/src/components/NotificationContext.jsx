import React, { createContext, useState, useEffect } from "react";
import { API_URL, BASE_URL } from "../config";

export const NotificationContext = createContext();

export const NotificationProvider = ({ children }) => {
  const [pendientes, setPendientes] = useState(0);
  const [mensajesNuevos, setMensajesNuevos] = useState(0);
  const [alertasPendientes, setAlertasPendientes] = useState(0);

  const usuarioId = Number(localStorage.getItem("usuarioId"));

  // === ALERTAS PENDIENTES ===
useEffect(() => {
  const fetchAlertas = async () => {
    try {
      const usuarioId = localStorage.getItem("usuarioId");
      if (!usuarioId) return;

      const res = await fetch(`${API_URL}/alertas/usuario/${usuarioId}`);
      const data = await res.json();

      // Crear un Set para combinar vehículo + tipo de alerta
      const pendientesUnicos = new Set();

      (data.alertas || []).forEach(a => {
        if (a.estado === "pendiente" || !a.fecha_resuelta) {
          // Asumiendo que a tiene: a.id_unidad y a.tipo_alerta
          const key = `${a.id_unidad}-${a.tipo_alerta}`;
          pendientesUnicos.add(key);
        }
      });

      setAlertasPendientes(pendientesUnicos.size);
    } catch (err) {
      console.error("Error cargando alertas pendientes:", err);
    }
  };

  fetchAlertas();
  const interval = setInterval(fetchAlertas, 15000);
  return () => clearInterval(interval);
}, []);

  // === SOLICITUDES PENDIENTES ===
  useEffect(() => {
    const fetchPendientes = async () => {
      try {
        const res = await fetch(`${API_URL}/solicitudes`);
        const data = await res.json();

        const pendientesCount = data.filter(s => s.estado === "pendiente").length;
        setPendientes(pendientesCount);
      } catch (err) {
        console.error(err);
      }
    };

    fetchPendientes();
    const interval = setInterval(fetchPendientes, 10000);
    return () => clearInterval(interval);
  }, []);

  // === MENSAJES NUEVOS ===
  useEffect(() => {
    const fetchMensajesNuevos = async () => {
      if (!usuarioId) return;

      try {
        const res = await fetch(`${BASE_URL}/mis_mensajes/${usuarioId}`);
        const data = await res.json();

        const nuevos = data.filter(m => m.id_usuario !== usuarioId).length;
        setMensajesNuevos(nuevos);
      } catch (err) {
        console.error(err);
      }
    };

    fetchMensajesNuevos();
    const intervalMensajes = setInterval(fetchMensajesNuevos, 10000);
    return () => clearInterval(intervalMensajes);
  }, [usuarioId]);

  // === PROVIDER FINAL ===
  return (
    <NotificationContext.Provider
      value={{
        pendientes,
        setPendientes,
        mensajesNuevos,
        setMensajesNuevos,
        alertasPendientes,     // ← FALTABA ESTO
        setAlertasPendientes,  // ← Y ESTO
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
};
