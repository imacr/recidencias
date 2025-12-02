import { useState, useEffect } from "react";
import Swal from "sweetalert2";
import Select from "react-select";
import { API_URL } from "../config";
import Modal from "../components/Modal";
import ModalFile from "../components/ModalFile";
import "./refrendo.css";

export default function RegistroPago() {
  const [unidades, setUnidades] = useState([]);
  const [pagos, setPagos] = useState([]);

  const [form, setForm] = useState({
    id_unidad: "",
    fecha_pago: "",
    monto: "",
    monto_refrendo: "",
    monto_tenencia: "",
    url_factura: null,
    observaciones: "",
    usuario: localStorage.getItem("usuarioId") || "",
  });

  const [tipoPago, setTipoPago] = useState("REFRENDO");
  const [canRegister, setCanRegister] = useState(false);
  const [paidRefrendo, setPaidRefrendo] = useState(false);
  const [paidTenencia, setPaidTenencia] = useState(false);
  const [loadingCheck, setLoadingCheck] = useState(false);

  const [showModal, setShowModal] = useState(false);
  const [editForm, setEditForm] = useState(null);
  const [showFileModal, setShowFileModal] = useState(false);
  const [fileUrl, setFileUrl] = useState(null);

  // ----------------------------
  // Filtros y búsqueda
  // ----------------------------
  const [filtroUnidad, setFiltroUnidad] = useState(null);
  const [filtroTipoPago, setFiltroTipoPago] = useState("");
  const [filtroFechaInicio, setFiltroFechaInicio] = useState("");
  const [filtroFechaFin, setFiltroFechaFin] = useState("");

  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPageOptions = [5, 10, 20, 50];
  const [filtroBusqueda, setFiltroBusqueda] = useState("");

  // ----------------------------
  // Cargar unidades
  // ----------------------------
  useEffect(() => {
    fetch(`${API_URL}/unidades`)
      .then(res => res.json())
      .then(data => setUnidades(data || []))
      .catch(() => Swal.fire("Error", "No se pudieron cargar las unidades", "error"));
  }, []);

  // ----------------------------
  // Obtener pagos con filtros
  // ----------------------------
  const fetchPagos = () => {
    const params = new URLSearchParams();
    if (filtroUnidad) params.append("unidad", filtroUnidad.value);
    if (filtroTipoPago) params.append("tipo_pago", filtroTipoPago);
    if (filtroFechaInicio) params.append("fecha_inicio", filtroFechaInicio);
    if (filtroFechaFin) params.append("fecha_fin", filtroFechaFin);

    fetch(`${API_URL}/refrendo_tenencia?${params.toString()}`)
      .then(res => res.json())
      .then(data => setPagos(data || []))
      .catch(() => Swal.fire("Error", "No se pudieron cargar los pagos", "error"));
  };

  useEffect(() => {
    fetchPagos();
  }, [filtroUnidad, filtroTipoPago, filtroFechaInicio, filtroFechaFin]);

  // ----------------------------
  // Manejo de cambios en formularios
  // ----------------------------
  const handleChange = (e, targetForm = form, setTargetForm = setForm) => {
    const { name, value, type, files } = e.target;
    if (type === "file") {
      setTargetForm(prev => ({ ...prev, url_factura: files[0] || null }));
    } else {
      setTargetForm(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleFechaChange = (e, targetForm = form, setTargetForm = setForm) => {
    const fecha = e.target.value;
    setTargetForm(prev => ({ ...prev, fecha_pago: fecha }));

    if (!fecha) {
      setTipoPago("REFRENDO");
      return;
    }
    const fechaPago = new Date(fecha);
    const limiteRefrendo = new Date(fechaPago.getFullYear(), 2, 31); // 31 marzo
    setTipoPago(fechaPago > limiteRefrendo ? "AMBOS" : "REFRENDO");
  };

  // ----------------------------
  // Validar unidad
  // ----------------------------
  const handleValidarUnidad = async () => {
    if (!form.id_unidad) return Swal.fire("Advertencia", "Selecciona una unidad", "warning");
    setLoadingCheck(true);
    try {
      const res = await fetch(`${API_URL}/refrendo_tenencia/check/${form.id_unidad}`);
      const data = await res.json();
      if (data.ok) {
        Swal.fire("Éxito", data.mensaje || "Se puede registrar pago", "success");
        setCanRegister(true);
        setPaidRefrendo(Boolean(data.refrendo));
        setPaidTenencia(Boolean(data.tenencia));
      } else {
        Swal.fire("Atención", data.mensaje || "No se puede registrar aún", "info");
        setCanRegister(false);
      }
    } catch (err) {
      console.error(err);
      Swal.fire("Error", "No se pudo validar la unidad", "error");
      setCanRegister(false);
    } finally {
      setLoadingCheck(false);
    }
  };

  // ----------------------------
  // Registrar pago
  // ----------------------------
  const handleRegistro = async () => {
    if (!canRegister) return Swal.fire("Advertencia", "Primero valida la unidad", "warning");
    if (!form.fecha_pago) return Swal.fire("Advertencia", "Fecha de pago es obligatoria", "warning");

    let tipo_pago = "REFRENDO";
    const fechaPago = new Date(form.fecha_pago);
    const limiteRefrendo = new Date(fechaPago.getFullYear(), 2, 31);
    if (fechaPago > limiteRefrendo) tipo_pago = "AMBOS";

    const fd = new FormData();
    fd.append("id_unidad", form.id_unidad);
    fd.append("fecha_pago", form.fecha_pago);
    fd.append("monto", form.monto || "0");
    fd.append("monto_refrendo", form.monto_refrendo || "0");
    fd.append("tipo_pago", tipo_pago);
    if (tipo_pago === "AMBOS") fd.append("monto_tenencia", form.monto_tenencia || "0");
    if (form.url_factura) fd.append("url_factura", form.url_factura);
    fd.append("observaciones", form.observaciones || "");
    fd.append("usuario", form.usuario);

    try {
      const res = await fetch(`${API_URL}/refrendo_tenencia`, { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) return Swal.fire("Error", data.error || "Error al registrar pago", "error");

      Swal.fire("Éxito", data.message || "Pago registrado", "success");

      setForm({
        id_unidad: "",
        fecha_pago: "",
        monto: "",
        monto_refrendo: "",
        monto_tenencia: "",
        url_factura: null,
        observaciones: "",
        usuario: localStorage.getItem("usuarioId") || "",
      });
      setTipoPago("REFRENDO");
      setCanRegister(false);
      setPaidRefrendo(false);
      setPaidTenencia(false);
      fetchPagos();
    } catch (err) {
      console.error(err);
      Swal.fire("Error", "No se pudo registrar el pago", "error");
    }
  };

  // ----------------------------
  // Editar pago
  // ----------------------------
  const handleEdit = (pago) => {
    setEditForm({ ...pago, usuario: localStorage.getItem("usuarioId") || "" });
    setShowModal(true);
  };

  const handleSaveEdit = async () => {
    if (!editForm?.fecha_pago) return Swal.fire("Advertencia", "Fecha de pago es obligatoria", "warning");

    const fd = new FormData();
    fd.append("id_pago", editForm.id_pago);
    fd.append("fecha_pago", editForm.fecha_pago);
    fd.append("monto_refrendo", editForm.monto_refrendo || 0);
    fd.append("monto_tenencia", editForm.monto_tenencia || 0);
    fd.append("observaciones", editForm.observaciones || "");
    fd.append("usuario", editForm.usuario);
    if (editForm.url_factura instanceof File) fd.append("url_factura", editForm.url_factura);

    try {
      const res = await fetch(`${API_URL}/refrendo_tenencia/${editForm.id_pago}`, { method: "PUT", body: fd });
      const data = await res.json();
      if (!res.ok) return Swal.fire("Error", data.error || "Error al actualizar pago", "error");

      Swal.fire("Éxito", data.message || "Pago actualizado", "success");
      setShowModal(false);
      setEditForm(null);
      fetchPagos();
    } catch (err) {
      console.error(err);
      Swal.fire("Error", "No se pudo actualizar el pago", "error");
    }
  };

  // ----------------------------
  // Filtrar y paginar
  // ----------------------------
  const pagosFiltrados = pagos.filter(p => {
    if (!filtroBusqueda) return true;
    const unidad = unidades.find(u => u.id_unidad === p.id_unidad);
    const placa = unidad?.vehiculo?.toLowerCase() || "";
    const folio = p.id_pago?.toString() || "";
    return placa.includes(filtroBusqueda.toLowerCase()) || folio.includes(filtroBusqueda);
  });

  const totalPages = Math.ceil(pagosFiltrados.length / itemsPerPage) || 1;
  const indexOfLast = currentPage * itemsPerPage;
  const indexOfFirst = indexOfLast - itemsPerPage;
  const pagosPaginados = pagosFiltrados.slice(indexOfFirst, indexOfLast);

  // ----------------------------
  // Render
  // ----------------------------
  return (
    <div className="unidades-container">
      <h1>Registrar Pago Refrendo / Tenencia</h1>

      <div className="form-container">
        {/* Unidad y Validar */}
        <div className="form-row" style={{ marginBottom: 15 }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Unidad:</label>
            <Select
              options={unidades.map(u => ({
                value: u.id_unidad,
                label: `${u.id_unidad} - ${u.marca} ${u.vehiculo} ${u.modelo}`
              }))}
              onChange={opt => setForm(prev => ({ ...prev, id_unidad: opt.value }))}
              value={form.id_unidad ? { value: form.id_unidad, label: (() => {
                const selected = unidades.find(u => u.id_unidad === form.id_unidad);
                return selected ? `${selected.id_unidad} - ${selected.marca} ${selected.vehiculo} ${selected.modelo}` : form.id_unidad;
              })() } : null}
              isClearable
              placeholder="Busca o selecciona unidad"
              isSearchable
            />
          </div>
          <button onClick={handleValidarUnidad} disabled={loadingCheck} style={{ height: 38, alignSelf: "end" }}>
            {loadingCheck ? "Validando..." : "Validar Unidad"}
          </button>
        </div>

        {/* Campos adicionales */}
        {canRegister && (
          <>
            <div className="form-row" style={{ marginBottom: 15 }}>
              <div className="form-group">
                <label>Fecha de pago:</label>
                <input type="date" name="fecha_pago" value={form.fecha_pago} onChange={handleFechaChange} />
              </div>
              <div className="form-group">
                <label>Monto general (opcional):</label>
                <input type="number" name="monto" value={form.monto} onChange={handleChange} />
              </div>
            </div>

            <div style={{ padding: 10, marginBottom: 10, background: "#f9f9f9", borderRadius: 6 }}>
              <h4>{tipoPago === "REFRENDO" ? "REFRENDO" : "REFRENDO / TENENCIA"}</h4>
              <div className="form-row">
                <div className="form-group">
                  <label>Monto Refrendo:</label>
                  <input type="number" name="monto_refrendo" value={form.monto_refrendo} onChange={handleChange} disabled={paidRefrendo} />
                </div>
                {tipoPago === "AMBOS" && (
                  <div className="form-group">
                    <label>Monto Tenencia:</label>
                    <input type="number" name="monto_tenencia" value={form.monto_tenencia} onChange={handleChange} disabled={paidTenencia} />
                  </div>
                )}
                <div className="form-group">
                  <label>Factura (PDF):</label>
                  <input type="file" name="url_factura" accept="application/pdf" onChange={handleChange} />
                </div>
              </div>
            </div>

            <div className="form-row" style={{ marginBottom: 15 }}>
              <div className="form-group" style={{ flex: 2 }}>
                <label>Observaciones:</label>
                <textarea name="observaciones" value={form.observaciones} onChange={handleChange}></textarea>
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Usuario:</label>
                <input name="usuario" value={form.usuario} disabled />
              </div>
            </div>

            <div style={{ textAlign: "right" }}>
              <button className="update-btn" onClick={handleRegistro}>Registrar Pago</button>
            </div>
          </>
        )}
      </div>

      {/* Filtros y búsqueda */}
      <div className="filtros-container" style={{ display: "flex", gap: 10, marginBottom: 20, flexWrap: "wrap" }}>
        <label className='pagination-label'>
          Mostrar:
          <select className="pagination-select"
            value={itemsPerPage}
            onChange={e => { setItemsPerPage(Number(e.target.value)); setCurrentPage(1); }}
          >
            {itemsPerPageOptions.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        </label>



        <div style={{ display: "flex", flexDirection: "column" }}>
          <label>Filtrar por unidad</label>
          <Select
            options={unidades.map(u => ({ value: u.id_unidad, label: `${u.id_unidad} - ${u.marca} ${u.vehiculo}` }))}
            value={filtroUnidad}
            onChange={setFiltroUnidad}
            isClearable
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          <label>Filtrar por tipo de pago</label>
          <select value={filtroTipoPago} onChange={e => setFiltroTipoPago(e.target.value)}>
            <option value="">Todos los tipos</option>
            <option value="REFRENDO">Refrendo</option>
            <option value="TENENCIA">Tenencia</option>
            <option value="AMBOS">Ambos</option>
          </select>
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          <label>Fecha inicio</label>
          <input type="date" value={filtroFechaInicio} onChange={e => setFiltroFechaInicio(e.target.value)} />
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          <label>Fecha fin</label>
          <input type="date" value={filtroFechaFin} onChange={e => setFiltroFechaFin(e.target.value)} />
        </div>

        <div style={{ display: "flex", flexDirection: "column", justifyContent: "flex-end" }}>
          <button onClick={() => { 
            setFiltroUnidad(null); 
            setFiltroTipoPago(""); 
            setFiltroFechaInicio(""); 
            setFiltroFechaFin(""); 
            setFiltroBusqueda("");
          }}>
            Limpiar filtros
          </button>
        </div>
      </div>

      {/* Tabla de pagos */}
      <div className="table-wrapper">
        <table className="elegant-table">
          <thead>
            <tr>
              <th>ID Unidad</th>
              <th>Vehículo</th>
              <th>Modelo</th>
              <th>Fecha Pago</th>
              <th>Tipo Pago</th>
              <th>Monto Refrendo</th>
              <th>Monto Tenencia</th>
              <th>Factura</th>
              <th>Usuario</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {pagosPaginados.length === 0 ? (
              <tr>
                <td colSpan={10} className="mensaje-estado">No hay pagos registrados</td>
              </tr>
            ) : (
              pagosPaginados.map(pago => {
                const unidad = unidades.find(u => u.id_unidad === pago.id_unidad) || {};
                return (
                  <tr key={pago.id_pago}>
                    <td>{unidad.id_unidad || pago.id_unidad}</td>
                    <td>{unidad.marca} {unidad.vehiculo}</td>
                    <td>{unidad.modelo}</td>
                    <td>{pago.fecha_pago || "-"}</td>
                    <td>{pago.tipo_pago || "-"}</td>
                    <td>{pago.monto_refrendo?.toFixed(2) || "-"}</td>
                    <td>{pago.monto_tenencia?.toFixed(2) || "-"}</td>
                    <td>
                      {pago.url_factura ? (
                        <button className="btn btn-outline-danger btn-sm"
                          onClick={() => { setFileUrl(`${API_URL}/${pago.url_factura}`); setShowFileModal(true); }}
                        >
                          Ver PDF
                        </button>
                      ) : "-"}
                    </td>
                    <td>{pago.usuario || "-"}</td>
                    <td>
                      <button onClick={() => handleEdit(pago)}>Editar</button>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      <div className="pagination">
        <button onClick={() => setCurrentPage(p => Math.max(p - 1, 1))} disabled={currentPage === 1}><i className="fa-solid fa-arrow-left"></i></button>
        <span>Página {currentPage} de {totalPages}</span>
        <button onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))} disabled={currentPage === totalPages}><i className="fa-solid fa-arrow-right"></i></button>
      </div>

      {/* Modal de edición */}
      {showModal && editForm && (
  <Modal title="Editar Pago" onClose={() => setShowModal(false)}>
    <div className="form-container">
      {/* Fecha de pago y monto general */}
      <div className="form-row" style={{ marginBottom: 15 }}>
        <div className="form-group">
          <label>Fecha de pago:</label>
          <input
            type="date"
            name="fecha_pago"
            value={editForm.fecha_pago}
            onChange={e => {
              const fecha = e.target.value;
              setEditForm(prev => ({ ...prev, fecha_pago: fecha }));

              // Actualizar tipo de pago automáticamente
              if (!fecha) return;
              const fechaPago = new Date(fecha);
              const limiteRefrendo = new Date(fechaPago.getFullYear(), 2, 31);
              setEditForm(prev => ({
                ...prev,
                tipo_pago: fechaPago > limiteRefrendo ? "AMBOS" : "REFRENDO",
              }));
            }}
          />
        </div>
        <div className="form-group">
          <label>Monto general (opcional):</label>
          <input
            type="number"
            name="monto"
            value={editForm.monto || ""}
            onChange={e => setEditForm(prev => ({ ...prev, monto: e.target.value }))}
          />
        </div>
      </div>

      {/* Refrendo / Tenencia */}
      <div style={{ padding: 10, marginBottom: 10, background: "#f9f9f9", borderRadius: 6 }}>
        <h4>{editForm.tipo_pago === "REFRENDO" ? "REFRENDO" : "REFRENDO / TENENCIA"}</h4>
        <div className="form-row">
          <div className="form-group">
            <label>Monto Refrendo:</label>
            <input
              type="number"
              name="monto_refrendo"
              value={editForm.monto_refrendo}
              onChange={e => setEditForm(prev => ({ ...prev, monto_refrendo: e.target.value }))}
              disabled={editForm.paidRefrendo}
            />
          </div>
          {editForm.tipo_pago === "AMBOS" && (
            <div className="form-group">
              <label>Monto Tenencia:</label>
              <input
                type="number"
                name="monto_tenencia"
                value={editForm.monto_tenencia}
                onChange={e => setEditForm(prev => ({ ...prev, monto_tenencia: e.target.value }))}
                disabled={editForm.paidTenencia}
              />
            </div>
          )}
          <div className="form-group">
            <label>Factura (PDF):</label>
            <input
              type="file"
              name="url_factura"
              accept="application/pdf"
              onChange={e => setEditForm(prev => ({ ...prev, url_factura: e.target.files[0] }))}
            />
          </div>
        </div>
      </div>

      {/* Observaciones y usuario */}
      <div className="form-row" style={{ marginBottom: 15 }}>
        <div className="form-group" style={{ flex: 2 }}>
          <label>Observaciones:</label>
          <textarea
            name="observaciones"
            value={editForm.observaciones}
            onChange={e => setEditForm(prev => ({ ...prev, observaciones: e.target.value }))}
          />
        </div>
        <div className="form-group" style={{ flex: 1 }}>
          <label>Usuario:</label>
          <input name="usuario" value={editForm.usuario} disabled />
        </div>
      </div>

      {/* Botón de guardar */}
      <div style={{ textAlign: "right" }}>
        <button className="update-btn" onClick={handleSaveEdit}>Guardar Cambios</button>
      </div>
    </div>
  </Modal>
)}


      {/* Modal para PDF */}
      {showFileModal && fileUrl && (
        <ModalFile url={fileUrl} onClose={() => setShowFileModal(false)} />
      )}
    </div>
  );
}
