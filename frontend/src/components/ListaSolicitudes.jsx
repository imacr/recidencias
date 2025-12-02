import React, { useState, useEffect, useContext } from "react";
import Swal from "sweetalert2";
import { API_URL } from "../config";
import { NotificationContext } from "./NotificationContext"; 
import Modal from "./Modal"; // Importa tu modal existente
import "./SolicitudForm.css";

export default function ListaSolicitudes() {
  const [solicitudes, setSolicitudes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const { setPendientes } = useContext(NotificationContext);

  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);
  const itemsPerPageOptions = [5, 10, 15, 20];

  // Para el modal
  const [modalOpen, setModalOpen] = useState(false);
  const [solicitudSeleccionada, setSolicitudSeleccionada] = useState(null);
  const [respuestas, setRespuestas] = useState({});
  const [archivos, setArchivos] = useState({});
  const usuarioId = localStorage.getItem("usuarioId"); // admin, usuario o chofer

// Agrega al inicio de tu componente
  const [modalArchivo, setModalArchivo] = useState(null);
  useEffect(() => {
    fetchSolicitudes();
  }, []);

  const fetchSolicitudes = async () => {
    try {
      const res = await fetch(`${API_URL}/solicitudes`);
      if (!res.ok) throw new Error("Error al cargar solicitudes");
      const data = await res.json();
      data.sort((a, b) => new Date(b.fecha_solicitud) - new Date(a.fecha_solicitud));
      setSolicitudes(data);

      const pendientesCount = data.filter(s => s.estado === "pendiente").length;
      setPendientes(pendientesCount);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Aprobación
  const handleAprobar = async (id, aprobar) => {
    try {
      const res = await fetch(`${API_URL}/solicitudes/${id}/aprobar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ aprobar }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.msg || "Error al procesar solicitud");

      Swal.fire("Éxito", data.msg, "success");

      setSolicitudes(prev => {
        const nuevos = prev.filter(s => s.id_solicitud !== id);
        const pendientesCount = nuevos.filter(s => s.estado === "pendiente").length;
        setPendientes(pendientesCount);
        return nuevos;
      });

    } catch (err) {
      Swal.fire("Error", err.message || "No se pudo procesar la solicitud", "error");
    }
  };

  // Rechazo con mensaje
  const handleRechazar = async (id) => {
    try {
      const { value: mensaje, isConfirmed } = await Swal.fire({
        title: "Motivo del rechazo",
        input: "textarea",
        inputPlaceholder: "Escribe el motivo del rechazo...",
        showCancelButton: true,
      });

      if (!isConfirmed) return;
      if (!mensaje || mensaje.trim() === "") {
        Swal.fire("Error", "Debes escribir un mensaje antes de rechazar.", "warning");
        return;
      }

      // Guardar mensaje
      const msgRes = await fetch(`${API_URL}/solicitudes_mensajes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id_solicitud: id,
          id_usuario: usuarioId,
          mensaje
        }),
      });
      const msgData = await msgRes.json();
      if (!msgRes.ok) throw new Error(msgData.msg || "Error enviando mensaje");

      // Marcar como rechazada
      const res = await fetch(`${API_URL}/solicitudes/${id}/rechazar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ razon_rechazo: mensaje }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.msg || "Error actualizando solicitud");

      Swal.fire("Éxito", "Rechazo enviado al chofer con mensaje", "success");
      fetchSolicitudes();

    } catch (err) {
      Swal.fire("Error", err.message || "No se pudo enviar el mensaje", "error");
    }
  };

  // Abrir modal y cargar mensajes
  const abrirChat = async (solicitud) => {
    try {
      const res = await fetch(`${API_URL}/solicitudes/${solicitud.id_solicitud}/mensajes_admin`);
      if (!res.ok) throw new Error("Error cargando chat");
      const data = await res.json(); // array con todos los mensajes

      setSolicitudSeleccionada({ ...solicitud, mensajes: data });
      setModalOpen(true);
    } catch (err) {
      Swal.fire("Error", err.message, "error");
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
    formData.append("id_usuario", usuarioId);
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

      abrirChat(solicitudSeleccionada);
    } catch (err) {
      Swal.fire("Error", err.message || "No se pudo enviar respuesta", "error");
    }
  };

  if (loading) return <p>Cargando solicitudes...</p>;
  if (error) return <p>Error: {error}</p>;
  if (solicitudes.length === 0) return <p>No hay solicitudes registradas</p>;

  const totalPages = Math.ceil(solicitudes.length / itemsPerPage);
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = solicitudes.slice(indexOfFirstItem, indexOfLastItem);

  return (
    <div className="unidades-container">
      <h1><i className="fa-solid fa-car-side"></i> Registro de Solicitudes</h1>
      <div className="pagination-controls mb-2 flex justify-between items-center">
        <label className="pagination-label flex items-center">
          Mostrar:
          <select
            className="pagination-select ml-2 border rounded px-2 py-1"
            value={itemsPerPage}
            onChange={e => { setItemsPerPage(Number(e.target.value)); setCurrentPage(1); }}
          >
            {itemsPerPageOptions.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="table-wrapper overflow-x-auto">
        <table className="elegant-table min-w-full border-collapse">
          <thead className="bg-blue-600 text-white">
            <tr>
              <th>Chofer</th> {/* nueva columna */}
              <th>Unidad</th>
              <th>Pieza</th>
              <th>Marca</th>
              <th>Servicio</th>
              <th>Descripción</th>
              <th>Estado</th>
              <th>Acciones</th>
              <th>Chat</th>
            </tr>
          </thead>
          <tbody>
            {currentItems.map((s, index) => (
              <tr key={s.id_solicitud} className={index % 2 === 0 ? "bg-gray-100" : "bg-white"}>
              <td className="border px-4 py-2">{s.chofer?.nombre || "Sin asignar"}</td>

                <td className="border px-4 py-2">{s.unidad}</td>
                <td className="border px-4 py-2">{s.pieza}</td>
                <td className="border px-4 py-2">{s.marca}</td>
                <td className="border px-4 py-2">{s.tipo_servicio}</td>
                <td className="border px-4 py-2">{s.descripcion}</td>
                <td className="border px-4 py-2 font-semibold">{s.estado}</td>
                <td className="border px-4 py-2">
                  {s.estado === "pendiente" && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleAprobar(s.id_solicitud, true)}
                      >
                        Aceptar
                      </button>
                      <button
                        onClick={() => handleRechazar(s.id_solicitud)}
                      >
                        Rechazar
                      </button>
                    </div>
                  )}
                </td>

                <td className="border px-4 py-2">
                  <button
                    onClick={() => abrirChat(s)}
                  >
                    Ver Chat
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>


{modalOpen && solicitudSeleccionada && (
  <Modal onClose={() => setModalOpen(false)}>
    <h2>Chat de solicitud #{solicitudSeleccionada.id_solicitud}</h2>
    <div
      className="chat-mensajes"
      style={{
        maxHeight: '400px',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px'
      }}
    >
      {solicitudSeleccionada.mensajes.map(m => {
        const esMiMensaje = String(m.id_usuario) === String(usuarioId);
        let colorBurbuja = m.rol === "admin" ? "azul" : m.rol === "usuario" ? "verde" : "gris";

        // extensión del archivo
        let extension = "";
        if (m.archivo_adjunto) {
          const parts = m.archivo_adjunto.split(".");
          extension = parts[parts.length - 1].toLowerCase();
        }

        const urlArchivo = m.archivo_adjunto ? `${API_URL}/uploads/mensajes/${m.archivo_adjunto}` : null;

        return (
          <div
            key={m.id_mensaje}
            className={`chat-bubble ${esMiMensaje ? "derecha" : "izquierda"} ${colorBurbuja}`}
            style={{ maxWidth: '80%' }}
          >
            <strong className="chat-user">{m.usuario}</strong>

            {/* Archivos adjuntos con click para ampliar */}
            {m.archivo_adjunto && (
              <div className="chat-archivo" style={{ margin: '5px 0', cursor: 'pointer' }}>
                {["jpg","jpeg","png","gif"].includes(extension) && (
                  <img
                    src={urlArchivo}
                    alt="Adjunto"
                    style={{ width: '100%', maxHeight: '300px', objectFit: 'contain' }}
                    onClick={() => setModalArchivo({ url: urlArchivo, ext: extension })}
                  />
                )}
                {["mp4","webm","ogg"].includes(extension) && (
                  <video
                    controls
                    style={{ width: '100%', maxHeight: '300px' }}
                    onClick={() => setModalArchivo({ url: urlArchivo, ext: extension })}
                  >
                    <source src={urlArchivo} type={`video/${extension}`} />
                  </video>
                )}
                {extension === "pdf" && (
                  <iframe
                    src={urlArchivo}
                    width="100%"
                    height="300px"
                    title="PDF Adjunto"
                    onClick={() => setModalArchivo({ url: urlArchivo, ext: extension })}
                    style={{ cursor: 'pointer' }}
                  />
                )}
              </div>
            )}

            {m.mensaje && <p style={{ margin: '5px 0' }}>{m.mensaje}</p>}
            <span className="chat-date" style={{ fontSize: '0.8em', color: '#555' }}>
              {new Date(m.fecha).toLocaleString()}
            </span>
          </div>
        );
      })}
    </div>

    {/* Formulario de respuesta */}
    <div className="respuesta-form mt-2" style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
      <textarea
        placeholder="Escribe tu respuesta..."
        value={respuestas[solicitudSeleccionada.id_solicitud] || ""}
        onChange={e =>
          setRespuestas(prev => ({ ...prev, [solicitudSeleccionada.id_solicitud]: e.target.value }))
        }
        rows={2}
        style={{ width: '100%', padding: '5px', resize: 'vertical' }}
      />
      <input
        type="file"
        accept="image/*,video/*,application/pdf"
        onChange={e =>
          setArchivos(prev => ({ ...prev, [solicitudSeleccionada.id_solicitud]: e.target.files[0] }))
        }
      />
      <button
        onClick={() => handleResponder(solicitudSeleccionada.id_solicitud)}
        style={{ marginTop: '5px' }}
      >
        Enviar
      </button>
    </div>

    {/* Modal de previsualización de archivo */}
    {modalArchivo && (
      <div 
        className="modal-overlay" 
        style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 99999
        }}
        onClick={() => setModalArchivo(null)}
      >
        <div 
          className="modal-content"
          onClick={e => e.stopPropagation()}
          style={{ position: 'relative' }}
        >
          <button
            onClick={() => setModalArchivo(null)}
            style={{
              position: 'absolute', top: 5, right: 5, fontSize: '1.5rem', color: 'white', background: 'none', border: 'none', cursor: 'pointer'
            }}
          >
            ×
          </button>
          {["jpg","jpeg","png","gif"].includes(modalArchivo.ext) && (
            <img src={modalArchivo.url} alt="Archivo" style={{ maxWidth: '90vw', maxHeight: '90vh', objectFit: 'contain' }} />
          )}
          {["mp4","webm","ogg"].includes(modalArchivo.ext) && (
            <video src={modalArchivo.url} controls autoPlay style={{ maxWidth: '90vw', maxHeight: '90vh' }} />
          )}
          {modalArchivo.ext === "pdf" && (
            <iframe src={modalArchivo.url} style={{ width: '80vw', height: '80vh', border: 'none' }} title="PDF" />
          )}
        </div>
      </div>
    )}
  </Modal>
)}



      {totalPages > 1 && (
        <div className="pagination flex justify-center items-center mt-3 gap-4">
          <button
            onClick={() => setCurrentPage(p => Math.max(p - 1, 1))}
            disabled={currentPage === 1}
            className="px-3 py-1 bg-gray-300 rounded disabled:opacity-50"
          >
            <i className="fa-solid fa-arrow-left"></i>
          </button>
          <span>Página {currentPage} de {totalPages}</span>
          <button
            onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))}
            disabled={currentPage === totalPages}
            className="px-3 py-1 bg-gray-300 rounded disabled:opacity-50"
          >
            <i className="fa-solid fa-arrow-right"></i>
          </button>
        </div>
      )}
    </div>
  );
}
