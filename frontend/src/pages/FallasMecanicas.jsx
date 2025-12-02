import React, { useEffect, useState } from "react";
import Swal from "sweetalert2";
import Modal from "../components/Modal";
import ModalFile from "../components/ModalFile";
import { BASE_URL } from "../config";
import './Unidades.css'; // Aquí va todo el CSS que incluiremos abajo

const FallasMecanicas = () => {
  const [fallas, setFallas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalFile, setModalFile] = useState(null);
  const [fallaToEdit, setFallaToEdit] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalDetalle, setModalDetalle] = useState(null);
  const [lugares, setLugares] = useState([]);
  const [unidades, setUnidades] = useState([]);
  const [piezas, setPiezas] = useState([]);
  const [marcas, setMarcas] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);
  const itemsPerPageOptions = [5, 10, 20];

  const [formFalla, setFormFalla] = useState({
    id_lugar: '',
    proveedor: '',
    tipo_pago: '',
    costo: '',
    tiempo_uso_pieza: '',
    observaciones: '',
    aplica_poliza: false,
    comprobanteFile: null,
    descripcion: '',
    tipo_servicio: '',
    id_unidad: '',
    id_pieza: '',
    id_marca: ''
  });

  const API_URL = `${BASE_URL}/fallas`;

  // Fetch fallas
  const fetchFallas = async () => {
    try {
      const res = await fetch(API_URL);
      if (!res.ok) throw new Error("Error al cargar fallas");
      const data = await res.json();
      setFallas(data);
    } catch (err) {
      console.error(err);
      setFallas([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchFallas(); }, []);

  // Fetch lugares
  useEffect(() => {
    const fetchLugares = async () => {
      try {
        const res = await fetch(`${BASE_URL}/lugares`);
        if (!res.ok) throw new Error("Error al cargar lugares");
        const data = await res.json();
        setLugares(data);
      } catch (err) {
        console.error(err);
        setLugares([]);
      }
    };
    fetchLugares();
  }, []);

  // Fetch unidades, piezas, marcas
  useEffect(() => {
    Promise.all([
      fetch(`${BASE_URL}/unidades`).then(r => r.json()),
      fetch(`${BASE_URL}/piezas`).then(r => r.json()),
      fetch(`${BASE_URL}/marcas`).then(r => r.json())
    ])
    .then(([u, p, m]) => {
      setUnidades(u);
      setPiezas(p);
      setMarcas(m);
    })
    .catch(console.error);
  }, []);

  const openModal = (falla = null) => {
    setFallaToEdit(falla);
    setFormFalla({
      id_lugar: falla?.id_lugar?.toString() || '',
      proveedor: falla?.proveedor || '',
      tipo_pago: falla?.tipo_pago || '',
      costo: falla?.costo || '',
      tiempo_uso_pieza: falla?.tiempo_uso_pieza || '',
      observaciones: falla?.observaciones || '',
      aplica_poliza: falla?.aplica_poliza || false,
      descripcion: falla?.descripcion || '',
      tipo_servicio: falla?.tipo_servicio || '',
      id_unidad: falla?.id_unidad || '',
      id_pieza: falla?.id_pieza || '',
      id_marca: falla?.id_marca || '',
      comprobanteFile: null
    });
    setShowModal(true);
  };

  const agregarOActualizarFalla = (fallaActualizada) => {
    setFallas(prev =>
      prev.some(f => f.id_falla === fallaActualizada.id_falla)
        ? prev.map(f => f.id_falla === fallaActualizada.id_falla ? fallaActualizada : f)
        : [fallaActualizada, ...prev]
    );
  };

  const handleSubmitFalla = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    Object.entries(formFalla).forEach(([key, value]) => {
      if (key === 'comprobanteFile' && value) formData.append('comprobante', value);
      else formData.append(key, value);
    });

    try {
      let response, data;
      if (fallaToEdit) {
        response = await fetch(`${API_URL}/${fallaToEdit.id_falla}`, { method: 'PUT', body: formData });
        if (!response.ok) throw new Error("Error al actualizar la falla");
        data = await response.json();
      } else {
        response = await fetch(`${BASE_URL}/falla_admin`, { method: 'POST', body: formData });
        if (!response.ok) throw new Error("Error al crear la falla");
        data = await response.json();
      }
      agregarOActualizarFalla(data.falla || data);
      setShowModal(false);
      setFallaToEdit(null);
      Swal.fire({ title: '¡Éxito!', text: fallaToEdit ? 'Falla actualizada' : 'Falla creada', icon: 'success', confirmButtonColor: '#28a745' });
    } catch (err) {
      Swal.fire({ title: 'Error', text: err.message, icon: 'error', confirmButtonColor: '#d33' });
    }
  };

  const handleDeleteFalla = async (id_falla) => {
    const result = await Swal.fire({
      title: '¿Estás seguro?',
      text: "Esta acción eliminará la falla permanentemente.",
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      cancelButtonColor: '#3085d6',
      confirmButtonText: 'Sí, eliminar',
      cancelButtonText: 'Cancelar'
    });
    if (!result.isConfirmed) return;
    try {
      const response = await fetch(`${API_URL}/${id_falla}`, { method: 'DELETE' });
      if (!response.ok) throw new Error('Error al eliminar la falla');
      fetchFallas();
      Swal.fire({ title: '¡Éxito!', text: 'Falla eliminada', icon: 'success', confirmButtonColor: '#28a745' });
    } catch (err) {
      Swal.fire({ title: 'Error', text: err.message, icon: 'error', confirmButtonColor: '#d33' });
    }
  };

  if (loading) return <p>Cargando fallas...</p>;

  const indexOfLast = currentPage * itemsPerPage;
  const indexOfFirst = indexOfLast - itemsPerPage;
  const currentFallas = fallas.slice(indexOfFirst, indexOfLast);
  const totalPages = Math.ceil(fallas.length / itemsPerPage) || 1;

  return (
    <div className="garantias-container">
      <h1><i className="fa-solid fa-wrench"></i> Fallas Mecánicos</h1>

      <div className="pagination-controls">
        <label>
          Mostrar:
          <select value={itemsPerPage} onChange={e => { setItemsPerPage(Number(e.target.value)); setCurrentPage(1); }}>
            {itemsPerPageOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
          </select>
        </label>
        <button onClick={() => openModal()} className="btn-registrar-garantia">Registrar Falla</button>
      </div>

      <div className="table-wrapper">
        <table className="elegant-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Unidad</th>
              <th>Pieza</th>
              <th>Marca</th>
              <th>Tipo Servicio</th>
              <th>Lugar Reparación</th>
              <th>Proveedor</th>
              <th>Tipo Pago</th>
              <th>Costo</th>
              <th>Comprobante</th>
              <th>Fecha Falla</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {currentFallas.map(f => (
              <tr key={f.id_falla}>
                <td>{f.id_falla}</td>
                <td>{f.unidad}</td>
                <td>{f.pieza}</td>
                <td>{f.marca}</td>
                <td>{f.tipo_servicio}</td>
                <td>{f.lugar_reparacion}</td>
                <td>{f.proveedor}</td>
                <td>{f.tipo_pago}</td>
                <td>${f.costo?.toLocaleString()}</td>
                <td>{f.url_comprobante ? <button  className="btn btn-outline-danger btn-sm" onClick={() => setModalFile(`${BASE_URL}/${f.url_comprobante}`)}>Ver Comprobante</button> : '—'}</td>
                <td>{f.fecha_falla ? new Date(f.fecha_falla).toLocaleDateString() : "N/A"}</td>
                <td>
                  <div className="actions-container">
                    <button className="icon-details" onClick={() => setModalDetalle(f)}><i className="fa fa-eye"></i></button>
                    <button className="icon-edit" onClick={() => openModal(f)}><i className="fa fa-edit"></i></button>
                    <button className="icon-delete" onClick={() => handleDeleteFalla(f.id_falla)}><i className="fa fa-trash"></i></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      <div className="pagination">
        <button onClick={() => setCurrentPage(p => Math.max(p - 1, 1))} disabled={currentPage === 1}><i className="fa-solid fa-arrow-left"></i></button>
        <span>Página {currentPage} de {totalPages}</span>
        <button onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))} disabled={currentPage === totalPages}><i className="fa-solid fa-arrow-right"></i></button>
      </div>

      {/* Modal Crear/Editar Falla */}
      {showModal && (
        <Modal onClose={() => { setShowModal(false); setFallaToEdit(null); }}>
          <h2>{fallaToEdit ? 'Editar Falla' : 'Registrar Falla'}</h2>
          <form className="form-container" onSubmit={handleSubmitFalla}>
            <div className="form-row">
              <div className="form-group">
                <label>Unidad:</label>
                <select
                  name="id_unidad"
                  value={formFalla.id_unidad || ""}
                  onChange={e => setFormFalla(prev => ({ ...prev, id_unidad: e.target.value }))}
                >
                  <option value="">Seleccione una unidad</option>
                  {unidades.map(u => <option key={u.id_unidad} value={u.id_unidad}>{u.id_unidad} - {u.vehiculo} ({u.marca} {u.modelo})</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Pieza:</label>
                <select
                  name="id_pieza"
                  value={formFalla.id_pieza || ""}
                  onChange={e => setFormFalla(prev => ({ ...prev, id_pieza: e.target.value }))}
                >
                  <option value="">Seleccione una pieza</option>
                  {piezas.map(p => <option key={p.id_pieza} value={p.id_pieza}>{p.nombre_pieza}</option>)}
                </select>
              </div>
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label>Marca:</label>
                <select
                  name="id_marca"
                  value={formFalla.id_marca || ""}
                  onChange={e => setFormFalla(prev => ({ ...prev, id_marca: e.target.value }))}
                >
                  <option value="">Seleccione una marca</option>
                  {marcas.map(m => <option key={m.id_marca} value={m.id_marca}>{m.nombre_marca}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Lugar Reparación:</label>
                <select
                  name="id_lugar"
                  value={formFalla.id_lugar}
                  onChange={e => setFormFalla(prev => ({ ...prev, id_lugar: e.target.value }))}
                  required
                >
                  <option value="">Selecciona un lugar</option>
                  {lugares.map(l => <option key={l.id_lugar} value={l.id_lugar}>{l.nombre_lugar}</option>)}
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Proveedor:</label>
                <input name="proveedor" value={formFalla.proveedor} onChange={e => setFormFalla(prev => ({ ...prev, proveedor: e.target.value }))} required />
              </div>
              <div className="form-group">
              <label>Tipo Pago:</label>
              <select
                name="tipo_pago"
                value={formFalla.tipo_pago}
                onChange={e => setFormFalla(prev => ({ ...prev, tipo_pago: e.target.value }))}
                required
              >
                <option value="">Seleccione un tipo de pago</option>
                <option value="Efectivo">Efectivo</option>
                <option value="Crédito">Crédito</option>
                <option value="Transferencia">Transferencia</option>
              </select>
            </div>

            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Costo:</label>
                <input type="number" name="costo" value={formFalla.costo} onChange={e => setFormFalla(prev => ({ ...prev, costo: e.target.value }))} required />
              </div>
              <div className="form-group">
                <label>Tiempo de Uso Pieza:</label>
                <input name="tiempo_uso_pieza" value={formFalla.tiempo_uso_pieza} onChange={e => setFormFalla(prev => ({ ...prev, tiempo_uso_pieza: e.target.value }))} />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Observaciones:</label>
                <textarea name="observaciones" value={formFalla.observaciones} onChange={e => setFormFalla(prev => ({ ...prev, observaciones: e.target.value }))} />
              </div>
              <div className="form-group">
                <label>
                  Aplica Póliza:
                  <input type="checkbox" name="aplica_poliza" checked={formFalla.aplica_poliza} onChange={e => setFormFalla(prev => ({ ...prev, aplica_poliza: e.target.checked }))} />
                </label>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Comprobante (PDF):</label>
                <input type="file" name="comprobante" accept="application/pdf" onChange={e => setFormFalla(prev => ({ ...prev, comprobanteFile: e.target.files[0] || null }))} />
              </div>
            </div>

            <div className="modal-buttons">
              <button type="submit" className="btn-save">{fallaToEdit ? 'Guardar Cambios' : 'Registrar Falla'}</button>
              <button type="button" onClick={() => { setShowModal(false); setFallaToEdit(null); }}>Cancelar</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal Detalle */}
      {modalDetalle && (
        <Modal onClose={() => setModalDetalle(null)}>
          <h2 className="details-header">Detalles Falla ID {modalDetalle.id_falla}</h2>
          <div className="details-container">
            {Object.entries(modalDetalle).map(([key, value]) => {
              if (['id_falla', 'id_unidad', 'id_pieza', 'id_marca', 'id_lugar', 'url_comprobante'].includes(key)) return null;
              return (
                <div key={key} className="detail-item">
                  <strong>{key.replace(/_/g, ' ')}:</strong>
                  <span>{value ? value.toString() : 'N/A'}</span>
                </div>
              );
            })}
          </div>
          {modalDetalle.url_comprobante && (
            <p>
              <strong>Comprobante:</strong>{" "}
              <a href={`${BASE_URL}/${modalDetalle.url_comprobante}`} target="_blank" rel="noopener noreferrer">
                Ver PDF
              </a>
            </p>
          )}
          <div className="modal-buttons">
            <button onClick={() => setModalDetalle(null)}>Cerrar</button>
          </div>
        </Modal>
      )}

      {/* Modal PDF */}
      {modalFile && (
        <ModalFile onClose={() => setModalFile(null)} url={modalFile} />
      )}
    </div>
  );
};

export default FallasMecanicas;
