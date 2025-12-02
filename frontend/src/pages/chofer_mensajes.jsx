import React, { useEffect, useState, useContext } from "react";
import { BASE_URL } from "../config";
import { NotificationContext } from "../components/NotificationContext";
import "../components/MensajesChofer.css";

export default function MensajesChofer() {
  const [solicitudes, setSolicitudes] = useState([]);
  const [respuestas, setRespuestas] = useState({});
  const [archivos, setArchivos] = useState({});
  const usuarioId = Number(localStorage.getItem("usuarioId"));
  const { setMensajesNuevos } = useContext(NotificationContext);

  // Traer mensajes al cargar
  useEffect(() => {
    fetchMensajes();
  }, []);

  const fetchMensajes = async () => {
    try {
      const res = await fetch(`${BASE_URL}/mis_mensajes/${usuarioId}`);
      const data = await res.json();

      console.log("✅ Datos crudos recibidos del backend:", data);
      setSolicitudes(data);

      // Contar mensajes nuevos del admin
      const nuevos = data.reduce((acc, s) => {
        const adminMsgs = s.mensajes.filter(m => m.quien === "admin");
        console.log(`Mensajes admin en solicitud ${s.id_solicitud}:`, adminMsgs);
        return acc + adminMsgs.length;
      }, 0);
      console.log("Total mensajes nuevos del admin:", nuevos);
      setMensajesNuevos(nuevos);

    } catch (err) {
      console.error("Error al obtener mensajes:", err);
    }
  };

  const enviarMensaje = async (id_solicitud) => {
    const mensaje = respuestas[id_solicitud] || "";
    const archivo = archivos[id_solicitud] || null;

    if (!mensaje && !archivo) {
      alert("Debes escribir un mensaje o subir un archivo");
      return;
    }

    try {
      const formData = new FormData();
      formData.append("id_solicitud", id_solicitud);
      formData.append("id_usuario", usuarioId);
      if (mensaje) formData.append("mensaje", mensaje);
      if (archivo) formData.append("archivo_adjunto", archivo);

      const res = await fetch(`${BASE_URL}/solicitudes_mensajes/responder`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      console.log("Respuesta al enviar mensaje:", data);

      if (!res.ok) throw new Error(data.msg || "Error enviando mensaje");

      // Limpiar campos
      setRespuestas(prev => ({ ...prev, [id_solicitud]: "" }));
      setArchivos(prev => ({ ...prev, [id_solicitud]: null }));

      fetchMensajes();
    } catch (err) {
      console.error(err);
    }
  };

  const renderArchivo = (archivo_adjunto) => {
    console.log("Renderizando archivo:", archivo_adjunto);
    const ext = archivo_adjunto.split(".").pop().toLowerCase();
    const url = `${BASE_URL}/uploads/mensajes/${encodeURIComponent(archivo_adjunto)}`;
    console.log("URL del archivo:", url, "Extensión:", ext);

    if (["jpg", "jpeg", "png", "gif"].includes(ext)) {
      return <img src={url} alt="Adjunto" style={{ maxWidth: "100%", maxHeight: 300, objectFit: "contain" }} />;
    }

    if (["mp4", "webm", "ogg"].includes(ext)) {
      return (
        <video controls style={{ width: "100%", maxHeight: 300 }}>
          <source src={url} type={`video/${ext}`} />
          Tu navegador no soporta la reproducción de este video.
        </video>
      );
    }

    if (ext === "pdf") {
      return <iframe src={url} width="100%" height="300" title="PDF Adjunto" />;
    }

    return <a href={url} target="_blank" rel="noreferrer">Ver archivo</a>;
  };

  return (
    <div>
      <h2>Mensajes sobre tus solicitudes</h2>
      {solicitudes.map(solicitud => (
        <div key={solicitud.id_solicitud} style={{ marginBottom: "20px", border: "1px solid #ccc", padding: "10px", borderRadius: "5px" }}>
          <h4>Solicitud #{solicitud.id_solicitud} - Estado: {solicitud.estado}</h4>
          
          {solicitud.mensajes.map(m => (
            <div key={m.id_mensaje} style={{ marginBottom: 10 }}>
              <p><strong>{m.quien}:</strong> {m.mensaje}</p>

              {m.archivo_adjunto ? (
                <>
                  {console.log("Archivo adjunto encontrado:", m.archivo_adjunto)}
                  {renderArchivo(m.archivo_adjunto)}
                </>
              ) : console.log("No hay archivo adjunto en este mensaje")}

              <small>{new Date(m.fecha).toLocaleString()}</small>
            </div>
          ))}

          {/* Formulario para responder */}
          <div style={{ marginTop: 10 }}>
            <textarea
              placeholder="Responder con evidencia..."
              value={respuestas[solicitud.id_solicitud] || ""}
              onChange={e => setRespuestas(prev => ({ ...prev, [solicitud.id_solicitud]: e.target.value }))}
              rows={2}
              style={{ width: "100%", padding: "5px", resize: "vertical" }}
            />
            <input
              type="file"
              accept="image/*,video/*,application/pdf" // Permite imágenes, videos y PDFs
              onChange={e => setArchivos(prev => ({ ...prev, [solicitud.id_solicitud]: e.target.files[0] }))}
            />

            <button onClick={() => enviarMensaje(solicitud.id_solicitud)} style={{ marginTop: 5 }}>Enviar</button>
          </div>
        </div>
      ))}
    </div>
  );
}
