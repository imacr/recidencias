import React, { useState, useEffect } from "react";
import Swal from "sweetalert2";
import { API_URL } from "../config";
import "./MensajesChofer.css";

export default function MensajesChoferChat() {
  const [conversaciones, setConversaciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [respuestas, setRespuestas] = useState({});
  const [archivos, setArchivos] = useState({});

  useEffect(() => {
    fetchConversaciones();
  }, []);

  const fetchConversaciones = async () => {
    const idChofer = localStorage.getItem("usuarioId");
    const rol = localStorage.getItem("rol");

    if (!idChofer || rol !== "chofer") {
      setError("No tienes permisos para ver estos mensajes");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`${API_URL}/mis_mensajes/${idChofer}`);
      if (!res.ok) throw new Error("Error al cargar mensajes");
      const data = await res.json();

      // Solo solicitudes rechazadas
      const rechazadas = data.filter(s => s.estado === "rechazada" || s.estado === "pendiente");
      setConversaciones(rechazadas);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResponder = async (id_solicitud) => {
    const mensaje = respuestas[id_solicitud]?.trim();
    const archivo = archivos[id_solicitud];

    if (!mensaje && !archivo) {
      Swal.fire("Error", "Escribe un mensaje o sube un archivo antes de responder", "warning");
      return;
    }

    const formData = new FormData();
    formData.append("id_solicitud", id_solicitud);
    formData.append("id_usuario", localStorage.getItem("usuarioId"));
    if (mensaje) formData.append("mensaje", mensaje);
    if (archivo) formData.append("archivo", archivo);

    try {
      const res = await fetch(`${API_URL}/solicitudes_mensajes/responder`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.msg || "Error al enviar respuesta");

      Swal.fire("Éxito", "Respuesta enviada", "success");
      setRespuestas(prev => ({ ...prev, [id_solicitud]: "" }));
      setArchivos(prev => ({ ...prev, [id_solicitud]: null }));
      fetchConversaciones();
    } catch (err) {
      Swal.fire("Error", err.message || "No se pudo enviar respuesta", "error");
    }
  };

  if (loading) return <p>Cargando mensajes...</p>;
  if (error) return <p>Error: {error}</p>;
  if (conversaciones.length === 0) return <p>No hay mensajes rechazados</p>;

  return (
    <div className="chat-container">
      <h1>Mensajes de Solicitudes Rechazadas</h1>
      {conversaciones.map((solicitud) => (
        <div key={solicitud.id_solicitud} className="chat-solicitud">
          <h2>Solicitud #{solicitud.id_solicitud} - {solicitud.tipo_servicio}</h2>
          <div className="chat-mensajes">
            {solicitud.mensajes.map((m) => (
              <div
                key={m.id_mensaje}
                className={`chat-bubble ${m.quien === "admin" ? "admin" : "chofer"}`}
              >
                {m.archivo_adjunto && (
                  <img
                    src={`${API_URL}/uploads/mensajes/${m.archivo_adjunto}`}
                    alt="Evidencia"
                    className="chat-image"
                  />
                )}
                {m.mensaje && <p>{m.mensaje}</p>}
                <span className="chat-date">{new Date(m.fecha).toLocaleString()}</span>
              </div>
            ))}
          </div>

          {/* Formulario de respuesta siempre disponible */}
          <div className="respuesta-form">
            <textarea
              placeholder="Escribe tu respuesta..."
              value={respuestas[solicitud.id_solicitud] || ""}
              onChange={e =>
                setRespuestas(prev => ({ ...prev, [solicitud.id_solicitud]: e.target.value }))
              }
              rows={2}
              className="chat-textarea"
            />
            <input
              type="file"
              accept="image/*"
              onChange={e =>
                setArchivos(prev => ({ ...prev, [solicitud.id_solicitud]: e.target.files[0] }))
              }
            />
            <button
              className="chat-button"
              onClick={() => handleResponder(solicitud.id_solicitud)}
            >
              Enviar
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
