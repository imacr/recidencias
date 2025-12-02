import { useEffect, useState } from "react";
import Swal from "sweetalert2";
import Modal from "../components/Modal";
import ModalFile from "../components/ModalFile";
import { API_URL } from "../config";
import Select from "react-select";

import "./Unidades.css";
import "./Placas.css";

export default function Placas() {
  const [placas, setPlacas] = useState([]);
  const [unidades, setUnidades] = useState([]);
  const [edit, setEdit] = useState(null);
  const [form, setForm] = useState({});
  const [unidadValida, setUnidadValida] = useState(false);
  const [fileModalUrl, setFileModalUrl] = useState(null);
  const [page, setPage] = useState(1);
  const [itemsPerPageOptions] = useState([5, 10, 20]);
  const [itemsPerPage, setItemsPerPage] = useState(5);
  const [total, setTotal] = useState(0);
  const [filtroBusqueda, setFiltroBusqueda] = useState("");
  const [filtroUnidadTabla, setFiltroUnidadTabla] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = Math.ceil(total / itemsPerPage) || 1;

  useEffect(() => {
    fetchPlacas(currentPage, filtroBusqueda, filtroUnidadTabla);
  }, [currentPage, itemsPerPage, filtroBusqueda, filtroUnidadTabla]);

  useEffect(() => {
    fetchUnidades();
  }, []);

  const fetchPlacas = async (
    pageOverride = currentPage,
    search = filtroBusqueda,
    idUnidad = filtroUnidadTabla
  ) => {
    try {
      const params = new URLSearchParams();
      params.append("page", pageOverride);
      params.append("per_page", itemsPerPage);

      if (search) params.append("search", search);
      if (idUnidad) params.append("id_unidad", idUnidad);

      const res = await fetch(`${API_URL}/placas?${params.toString()}`);
      const data = await res.json();
      setPlacas(data.placas || []);
      setTotal(data.total || 0);
    } catch (err) {
      Swal.fire("Error", "No se pudieron cargar las placas", "error");
    }
  };

  const fetchUnidades = async () => {
    try {
      const res = await fetch(`${API_URL}/unidades`);
      const data = await res.json();
      setUnidades(data || []);
    } catch (err) {
      Swal.fire("Error", "No se pudieron cargar las unidades", "error");
    }
  };

  const verificarUnidad = async () => {
    if (!form.id_unidad)
      return Swal.fire("Advertencia", "Debes ingresar el ID de la unidad", "warning");

    const unidad = unidades.find(u => u.id_unidad.toString() === form.id_unidad.toString());
    if (!unidad) {
      setUnidadValida(false);
      return Swal.fire("Error", "La unidad no existe", "error");
    }

    try {
      const res = await fetch(`${API_URL}/placas?id_unidad=${form.id_unidad}`);
      const data = await res.json();
      const placasUnidad = data.placas || [];

      const hoy = new Date();
      let puedeRegistrar = true;

      for (const placa of placasUnidad) {
        if (!placa.fecha_vigencia) continue;
        const fechaVigencia = new Date(placa.fecha_vigencia);
        const diasRestantes = Math.ceil((fechaVigencia - hoy) / (1000 * 60 * 60 * 24));
        if (diasRestantes > 180) {
          puedeRegistrar = false;
          const fechaFormateada = new Intl.DateTimeFormat("es-MX", {
            day: "numeric",
            month: "long",
            year: "numeric"
          }).format(fechaVigencia);
          setUnidadValida(false);
          return Swal.fire({
            title: "Unidad válida ⚠️",
            html: `No puedes registrar nueva placa.<br><strong>Placa ${placa.placa} vigente hasta:</strong> ${fechaFormateada}`,
            icon: "info"
          });
        }
      }

      if (puedeRegistrar) {
        setUnidadValida(true);
        Swal.fire("Unidad válida ✅", "Puedes registrar nueva placa de reemplazo", "success");
      }
    } catch (err) {
      Swal.fire("Error", "No se pudo verificar la unidad", "error");
    }
  };

  const handleChange = (e) => {
    const { name, type, value, checked } = e.target;
    setForm({ ...form, [name]: type === "checkbox" ? checked : value });
  };

  const handleFileChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.files[0] });
  };

 const handleRegistro = async () => {
  if (!unidadValida)
    return Swal.fire("Advertencia", "Verifica primero la unidad", "warning");
  if (!form.placa || !form.fecha_vigencia)
    return Swal.fire("Advertencia", "Placa y fecha de vigencia son obligatorias", "warning");

  const fd = new FormData();
  Object.keys(form).forEach(k => {
    if (form[k] !== undefined && form[k] !== null) fd.append(k, form[k]);
  });

  // Agregar usuario logueado
  const usuarioId = localStorage.getItem("usuarioId");
  if (usuarioId) fd.append("usuarioId", usuarioId);

  try {
    const res = await fetch(`${API_URL}/placas/registrar`, { method: "POST", body: fd });
    if (!res.ok) {
      const err = await res.json();
      return Swal.fire("Error", err.error || "Error al registrar nueva placa", "error");
    }
    Swal.fire("Éxito", "Nueva placa registrada correctamente", "success");
    setForm({});
    setUnidadValida(false);
    fetchPlacas();
  } catch (err) {
    Swal.fire("Error", "No se pudo registrar la nueva placa", "error");
  }
};




  const handleEdit = (p) => {
    setEdit(p);
    setForm({
      ...p,
      id_unidad: p.id_unidad || "",
      placa: p.placa || "",
      folio: p.folio || "",
      fecha_expedicion: p.fecha_expedicion || "",
      fecha_vigencia: p.fecha_vigencia || "",
      monto_pago: p.monto_pago || "",
      url_placa_frontal: null,
      url_placa_trasera: null,
      comprobante: null,
      tarjeta_circulacion: null
    });
  };

  const handleActualizar = async () => {
    if (!edit) return;
    const fd = new FormData();
    Object.keys(form).forEach(k => {
      if (form[k] !== undefined && form[k] !== null) fd.append(k, form[k]);
    });

    try {
      const res = await fetch(`${API_URL}/placas/${edit.id_placa}`, { method: "PUT", body: fd });
      if (!res.ok) {
        const err = await res.json();
        return Swal.fire("Error", err.error || "Error al actualizar placa", "error");
      }
      Swal.fire("Éxito", "Placa actualizada correctamente", "success");
      setEdit(null);
      setForm({});
      fetchPlacas();
    } catch (err) {
      Swal.fire("Error", "No se pudo actualizar la placa", "error");
    }
  };

  const handleEliminar = async (id_placa) => {
    const result = await Swal.fire({
      title: "¿Seguro que quieres eliminar esta placa?",
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Sí, eliminar",
      cancelButtonText: "Cancelar"
    });
    if (!result.isConfirmed) return;

    try {
      const res = await fetch(`${API_URL}/placas/${id_placa}`, { method: "DELETE" });
      if (!res.ok) {
        const err = await res.json();
        return Swal.fire("Error", err.error || "Error al eliminar placa", "error");
      }
      Swal.fire("Éxito", "Placa eliminada correctamente", "success");
      fetchPlacas();
    } catch (err) {
      Swal.fire("Error", "No se pudo eliminar la placa", "error");
    }
  };

  return (
    <div className="unidades-container">
      <h1>Placas</h1>

      {/* Verificar Unidad */}
      <div className="d-flex gap-2 mb-3" style={{ alignItems: "flex-end" }}>
        <div style={{ width: "300px" }}>
          <label style={{ fontSize: "0.9rem" }}>Verificar unidad para reemplazo:</label>
          <Select
            options={unidades.map(u => ({ value: u.id_unidad, label: `${u.id_unidad} - ${u.marca} ${u.vehiculo} ${u.modelo}` }))}
            value={form.id_unidad ? { value: form.id_unidad, label: unidades.find(u => u.id_unidad === form.id_unidad) ? `${form.id_unidad} - ${unidades.find(u => u.id_unidad === form.id_unidad).marca} ${unidades.find(u => u.id_unidad === form.id_unidad).vehiculo}` : form.id_unidad } : null}
            onChange={opt => setForm(prev => ({ ...prev, id_unidad: opt ? opt.value : "" }))}
            isClearable
            isSearchable
            placeholder="Busca o selecciona unidad"
            styles={{ container: base => ({ ...base, width: "100%" }), control: base => ({ ...base, minHeight: 35 }), menu: base => ({ ...base, zIndex: 9999 }) }}
          />
        </div>

        <button type="button" className="btn btn-outline-danger" onClick={verificarUnidad} style={{ height: 35 }}>
          Verificar unidad
        </button>

        {unidadValida && <span style={{ marginLeft: 10, color: "green" }}>Unidad válida ✅</span>}
      </div>

      {/* Registro Nueva Placa */}
      {unidadValida && !edit && (
        <div className="form-registro-placa">
          <h3>Registrar Nueva Placa</h3>
          <div className="grid-placa">
            <div className="form-group"><label>Placa</label><input name="placa" value={form.placa || ""} onChange={handleChange} /></div>
            <div className="form-group"><label>Folio de la tarjeta de circulacion</label><input name="folio" value={form.folio || ""} onChange={handleChange} /></div>
            <div className="form-group"><label>Fecha Expedición</label><input type="date" name="fecha_expedicion" value={form.fecha_expedicion || ""} onChange={handleChange} /></div>
            <div className="form-group"><label>Fecha Vigencia</label><input type="date" name="fecha_vigencia" value={form.fecha_vigencia || ""} onChange={handleChange} /></div>
            <div className="form-group"><label>Monto Pago</label><input type="number" name="monto_pago" value={form.monto_pago || ""} onChange={handleChange} /></div>
            <div className="form-group"><label>placa Frontal</label><input type="file" name="url_placa_frontal" onChange={handleFileChange} /></div>
            <div className="form-group"><label>Trasera</label><input type="file" name="url_placa_trasera" onChange={handleFileChange} /></div>
            <div className="form-group"><label>Comprobante del pago</label><input type="file" name="comprobante" onChange={handleFileChange} /></div>
            <div className="form-group"><label>Tarjeta Circulación</label><input type="file" name="tarjeta_circulacion" onChange={handleFileChange} /></div>
          </div>
          <button className="btn-placa-registrar" onClick={handleRegistro}>Registrar</button>
        </div>
      )}

      {/* Filtros */}
      <label style={{ fontSize: "0.9rem" }}>Filtros:</label>
      <div className="filtros-container">
        <label className='pagination-label'>
          Mostrar:
          <select className="pagination-select"
            value={itemsPerPage}
            onChange={e => { setItemsPerPage(Number(e.target.value)); setCurrentPage(1); }}
          >
            {itemsPerPageOptions.map(opt => (<option key={opt} value={opt}>{opt}</option>))}
          </select>
        </label>

        <input
          type="text"
          placeholder="Buscar placa o folio..."
          value={filtroBusqueda}
          onChange={e => { setFiltroBusqueda(e.target.value); setPage(1); fetchPlacas(1, e.target.value, filtroUnidadTabla); }}
          style={{ width: 200 }}
        />

        <Select
          options={[{ value: "", label: "Todas las unidades" }, ...unidades.map(u => ({ value: u.id_unidad, label: `${u.id_unidad} - ${u.marca} ${u.vehiculo}` }))]}
          value={filtroUnidadTabla !== "" ? { value: filtroUnidadTabla, label: unidades.find(u => u.id_unidad === filtroUnidadTabla) ? `${filtroUnidadTabla} - ${unidades.find(u => u.id_unidad === filtroUnidadTabla).marca}` : filtroUnidadTabla } : { value: "", label: "Todas las unidades" }}
          onChange={opt => { const unidad = opt ? opt.value : ""; setFiltroUnidadTabla(unidad); setPage(1); fetchPlacas(1, filtroBusqueda, unidad); }}
          placeholder="Filtrar por unidad"
          isClearable
          isSearchable
          styles={{ container: base => ({ ...base, width: 250 }) }}
        />
      </div>

      {/* Tabla */}
      <div className="table-wrapper">
        <table className="elegant-table">
          <thead>
            <tr>
              <th>ID</th><th>Unidad</th><th>Placa</th><th>Folio</th><th>Expedición</th><th>Vigencia</th><th>Pago</th><th>Frontal</th><th>Trasera</th><th>Comprobante</th><th>Tarjeta</th><th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {placas.map(p => (
              <tr key={p.id_placa}>
                <td>{p.id_placa}</td>
                <td>{p.id_unidad || "N/A"}</td>
                <td>{p.placa}</td>
                <td>{p.folio}</td>
                <td>{p.fecha_expedicion ? new Date(p.fecha_expedicion).toLocaleDateString('es-MX') : "N/A"}</td>
                <td>{p.fecha_vigencia ? new Date(p.fecha_vigencia).toLocaleDateString('es-MX') : "N/A"}</td>
                <td>{p.monto_pago  ? `$${p.monto_pago}` :  "N/A"}</td>
                <td>{p.url_placa_frontal ? <button className="btn btn-outline-danger btn-sm" onClick={() => setFileModalUrl(`${API_URL}/${p.url_placa_frontal}`)}>Ver PDF</button> : "N/A"}</td>
                <td>{p.url_placa_trasera ? <button className="btn btn-outline-danger btn-sm" onClick={() => setFileModalUrl(`${API_URL}/${p.url_placa_trasera}`)}>Ver PDF</button> : "N/A"}</td>
                <td>{p.url_comprobante_pago ? <button className="btn btn-outline-danger btn-sm" onClick={() => setFileModalUrl(`${API_URL}/${p.url_comprobante_pago}`)}>Ver PDF</button> : "N/A"}</td>
                <td>{p.url_tarjeta_circulacion ? <button className="btn btn-outline-danger btn-sm" onClick={() => setFileModalUrl(`${API_URL}/${p.url_tarjeta_circulacion}`)}>Ver PDF</button> : "N/A"}</td>
                <td>
                  <div className="actions-container">
                    <button onClick={() => handleEdit(p)}><i className="fa-solid fa-pen-to-square icon-edit"></i></button>
                    <button onClick={() => handleEliminar(p.id_placa)}><i className="fa-solid fa-trash icon-delete"></i></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal Edición */}
      {edit && (
        <Modal onClose={() => setEdit(null)}>
          <div className="edit-placa-container">
            <h2>Editar Placa {edit.id_placa}</h2>
            <div><label>Unidad:</label>
              <select name="id_unidad" value={form.id_unidad} onChange={handleChange}>
                <option value="">Seleccione unidad</option>
                {unidades.map(u => <option key={u.id_unidad} value={u.id_unidad}>{u.vehiculo} {u.marca} {u.modelo}</option>)}
              </select>
            </div>
            <div><label>Placa:</label><input name="placa" value={form.placa} onChange={handleChange} /></div>
            <div><label>Folio de la tarjeta de circulacion:</label><input name="folio" value={form.folio} onChange={handleChange} /></div>
            <div><label>Fecha Expedición:</label><input type="date" name="fecha_expedicion" value={form.fecha_expedicion || ""} onChange={handleChange} /></div>
            <div><label>Fecha Vigencia:</label><input type="date" name="fecha_vigencia" value={form.fecha_vigencia || ""} onChange={handleChange} /></div>
            <div><label>Monto Pago:</label><input type="number" name="monto_pago" value={form.monto_pago || ""} onChange={handleChange} /></div>
            <div><label>Frontal:</label><input type="file" name="url_placa_frontal" onChange={handleFileChange} /></div>
            <div><label>Trasera:</label><input type="file" name="url_placa_trasera" onChange={handleFileChange} /></div>
            <div><label>Comprobante:</label><input type="file" name="comprobante" onChange={handleFileChange} /></div>
            <div><label>Tarjeta Circulación:</label><input type="file" name="tarjeta_circulacion" onChange={handleFileChange} /></div>
            <div style={{ marginTop: 10 }}>
              <button onClick={handleActualizar}>Actualizar</button>
              <button onClick={() => setEdit(null)} style={{ marginLeft: 5 }}>Cancelar</button>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal previsualización */}
      {fileModalUrl && <ModalFile url={fileModalUrl} onClose={() => setFileModalUrl(null)} />}

      {/* Paginación */}
      <div className="pagination">
        <button onClick={() => setCurrentPage(p => Math.max(p - 1, 1))} disabled={currentPage === 1}><i className="fa-solid fa-arrow-left"></i></button>
        <span>Página {currentPage} de {totalPages}</span>
        <button onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))} disabled={currentPage === totalPages}><i className="fa-solid fa-arrow-right"></i></button>
      </div>

    </div>
  );
}
