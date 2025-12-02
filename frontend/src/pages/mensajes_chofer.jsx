import React, { useEffect, useState, useContext, useRef } from "react";
import Swal from "sweetalert2";
import { BASE_URL } from "../config";
import { NotificationContext } from "../components/NotificationContext";
import "./MensajesChofer.css";

export default function MensajesChoferEpic() {
  const [solicitudes, setSolicitudes] = useState([]);
  const [respuestas, setRespuestas] = useState({});
  const [archivos, setArchivos] = useState({});
  const [modalArchivo, setModalArchivo] = useState(null);
  const usuarioId = Number(localStorage.getItem("usuarioId"));
  const { setMensajesNuevos } = useContext(NotificationContext);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchMensajes();
  }, []);

  const fetchMensajes = async () => {
    try {
      const res = await fetch(`${BASE_URL}/mis_mensajes/${usuarioId}`);
      const data = await res.json();
      setSolicitudes(data);

      const nuevos = data.reduce(
        (acc, s) => acc + s.mensajes.filter(m => m.quien === "admin").length,
        0
      );
      setMensajesNuevos(nuevos);
      scrollToBottom();
    } catch (err) {
      console.error("Error al obtener mensajes:", err);
    }
  };

  const enviarMensaje = async (id_solicitud) => {
    const mensaje = respuestas[id_solicitud] || "";
    const archivo = archivos[id_solicitud] || null;

    if (!mensaje && !archivo) {
      Swal.fire({
        icon: "warning",
        title: "¡Ups!",
        text: "Debes escribir un mensaje o subir un archivo",
      });
      return;
    }

    try {
      const formData = new FormData();
      formData.append("id_solicitud", id_solicitud);
      formData.append("id_usuario", usuarioId);
      if (mensaje) formData.append("mensaje", mensaje);
      if (archivo) formData.append("archivo", archivo);

      const res = await fetch(`${BASE_URL}/solicitudes_mensajes/responder`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.msg || "Error enviando mensaje");

      Swal.fire({
        icon: "success",
        title: "¡Enviado!",
        text: "Tu mensaje se envió correctamente",
        timer: 1500,
        showConfirmButton: false,
      });

      setRespuestas(prev => ({ ...prev, [id_solicitud]: "" }));
      setArchivos(prev => ({ ...prev, [id_solicitud]: null }));
      fetchMensajes();
    } catch (err) {
      console.error("Error al enviar mensaje:", err);
      Swal.fire({
        icon: "error",
        title: "Error",
        text: err.message,
      });
    }
  };

  const renderArchivo = (archivo_adjunto) => {
    const ext = archivo_adjunto.split(".").pop().toLowerCase();
    const url = `${BASE_URL}/uploads/mensajes/${encodeURIComponent(archivo_adjunto)}`;
    const openModal = () => setModalArchivo({ url, ext });

    if (["jpg", "jpeg", "png", "gif"].includes(ext)) {
      return (
        <div className="mensajes-chofer-archivo" onClick={openModal}>
          <img
            src={url}
            alt="Adjunto"
            style={{ maxHeight: "100%", maxWidth: "100%", objectFit: "contain" }}
          />
        </div>
      );
    }

    if (["mp4", "webm", "ogg"].includes(ext)) {
      return (
        <div className="mensajes-chofer-archivo" onClick={openModal}>
          <video
            src={url}
            style={{ maxHeight: "100%", maxWidth: "100%", objectFit: "contain" }}
            muted
            loop
          />
          <div className="mensajes-chofer-overlay-text">Click para ampliar</div>
        </div>
      );
    }

    if (ext === "pdf") {
      return (
        <div className="mensajes-chofer-archivo" onClick={openModal}>
          <iframe
            src={url}
            title="PDF Adjunto"
            style={{ width: "100%", height: "100%", pointerEvents: "none" }}
          />
          <div className="mensajes-chofer-overlay-text">Click para ampliar</div>
        </div>
      );
    }

    return (
      <a href={url} target="_blank" rel="noreferrer">
        Ver archivo
      </a>
    );
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="mensajes-chofer-container">
      {solicitudes.map((solicitud) => (
        <div key={solicitud.id_solicitud} className="mensajes-chofer-solicitud">
          <div className="mensajes-chofer-solicitud-header">
            <h3>
              Solicitud #{solicitud.id_solicitud} - Estado: {solicitud.estado}
            </h3>
          </div>

          <div className="mensajes-chofer-mensajes">
            {solicitud.mensajes.map((m) => (
              <div key={m.id_mensaje} className={`mensajes-chofer-bubble ${m.quien}`}>
                <p>{m.mensaje}</p>
                {m.archivo_adjunto && renderArchivo(m.archivo_adjunto)}
                <small>{new Date(m.fecha).toLocaleString()}</small>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="mensajes-chofer-footer">
            <textarea
              className="mensajes-chofer-textarea"
              placeholder="Escribe un mensaje o adjunta un archivo..."
              value={respuestas[solicitud.id_solicitud] || ""}
              onChange={(e) =>
                setRespuestas((prev) => ({
                  ...prev,
                  [solicitud.id_solicitud]: e.target.value,
                }))
              }
            />
            <div className="mensajes-chofer-footer-actions">
              <input
                type="file"
                accept="*/*"
                onChange={(e) =>
                  setArchivos((prev) => ({
                    ...prev,
                    [solicitud.id_solicitud]: e.target.files[0],
                  }))
                }
              />
              <button
                className="mensajes-chofer-button"
                onClick={() => enviarMensaje(solicitud.id_solicitud)}
              >
                Enviar
              </button>
            </div>
          </div>
        </div>
      ))}

      {modalArchivo && (
        <div className="mensajes-chofer-modal-overlay" onClick={() => setModalArchivo(null)}>
          <div className="mensajes-chofer-modal-content" onClick={(e) => e.stopPropagation()}>
            <button
              className="mensajes-chofer-modal-close"
              onClick={() => setModalArchivo(null)}
            >
              ×
            </button>

            {["jpg", "jpeg", "png", "gif"].includes(modalArchivo.ext) && (
              <img
                src={modalArchivo.url}
                alt="Archivo"
              />
            )}

            {["mp4", "webm", "ogg"].includes(modalArchivo.ext) && (
              <video
                src={modalArchivo.url}
                controls
                autoPlay
              />
            )}

            {modalArchivo.ext === "pdf" && (
              <div style={{ width: "80vw", height: "80vh", overflow: "auto", borderRadius: "10px" }}>
                <iframe
                  src={modalArchivo.url}
                  style={{ width: "100%", height: "100%", border: "none" }}
                  title="PDF"
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
