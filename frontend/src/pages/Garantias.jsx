import React, { useEffect, useState } from "react";
import './Unidades.css';
import './Garantias.css';
import Crudgarantias from './Garantias_CRUD';
import ModalFile from "../components/ModalFile";
import Swal from 'sweetalert2';
import { BASE_URL } from "../config"; 

const Garantias = () => {
  const [garantias, setGarantias] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalFile, setModalFile] = useState(null);
  const [garantiaToEdit, setGarantiaToEdit] = useState(null);

  // Paginación
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);
  const itemsPerPageOptions = [5, 10, 20, "Todos"];

  // Filtros
  const [filtroGeneral, setFiltroGeneral] = useState("");
  const [filtroInicio, setFiltroInicio] = useState("");
  const [filtroFin, setFiltroFin] = useState("");

  const API_URL = `${BASE_URL}/api/garantias`;

  // Traer todas las garantías al cargar
  useEffect(() => {
    let mounted = true;
    const fetchGarantias = async () => {
      try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error(`Error ${response.status}`);
        const data = await response.json();
        if (mounted) setGarantias(data);
      } catch (err) {
        setError(err.message);
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchGarantias();
    return () => mounted = false;
  }, []);

  // Función para agregar o actualizar garantía con alertas
  const agregarOActualizarGarantia = (garantia) => {
    const isUpdate = garantias.some(g => g.id_garantia === garantia.id_garantia);
    const title = isUpdate ? '¡Garantía actualizada!' : '¡Garantía registrada!';
    const text = isUpdate 
      ? 'Los datos de la garantía se han actualizado correctamente.'
      : 'La garantía se ha guardado correctamente.';
    const icon = 'success';

    Swal.fire({ title, text, icon, confirmButtonColor: '#0d6efd', confirmButtonText: 'Aceptar' })
      .then(() => window.location.reload());
  };

  // Eliminar garantía
  const handleDeleteGarantia = async (id_garantia) => {
    const result = await Swal.fire({
      title: '¿Estás seguro?',
      text: "Esta acción eliminará la garantía permanentemente.",
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      cancelButtonColor: '#3085d6',
      confirmButtonText: 'Sí, eliminar',
      cancelButtonText: 'Cancelar'
    });

    if (!result.isConfirmed) return;

    try {
      const response = await fetch(`${API_URL}/${id_garantia}`, { method: 'DELETE' });
      if (!response.ok) throw new Error('Error al eliminar la garantía');

      const data = await fetch(API_URL).then(r => r.json());
      setGarantias(data);

      Swal.fire({
        title: '¡Éxito!',
        text: 'Garantía eliminada correctamente',
        icon: 'success',
        iconColor: '#ca0808ff',
        confirmButtonColor: '#28a745'
      });
    } catch (err) {
      Swal.fire({ title: 'Error', text: err.message, icon: 'error', confirmButtonColor: '#d33' });
    }
  };

  if (loading) return <p>Cargando Pólizas...</p>;
  if (error) return <p>Error: {error}</p>;

  // --- FILTROS ---
  const garantiasFiltradas = garantias.filter(g => {
    const general = filtroGeneral.toLowerCase();
    const matchGeneral =
      g.id_unidad?.toString().includes(general) ||
      g.chofer_asignado?.toLowerCase().includes(general) ||
      g.aseguradora?.toLowerCase().includes(general) ||
      g.marca?.toLowerCase().includes(general) ||
      g.vehiculo?.toLowerCase().includes(general);

    const inicio = filtroInicio ? new Date(g.inicio_vigencia) >= new Date(filtroInicio) : true;
    const fin = filtroFin ? new Date(g.vigencia) <= new Date(filtroFin) : true;

    return matchGeneral && inicio && fin;
  });

  // --- PAGINACIÓN ---
  const indexOfLast = currentPage * itemsPerPage;
  const indexOfFirst = indexOfLast - itemsPerPage;
  const currentGarantias = garantiasFiltradas.slice(indexOfFirst, indexOfLast);
  const totalPages = Math.ceil(garantiasFiltradas.length / itemsPerPage);

  return (
    <div className="unidades-container">
      <h1><i className="fa-solid fa-file-shield"></i> Pólizas de Seguro</h1>

      {/* Controles de filtros y paginación */}
      <div className="pagination-controls">
        <label>
          Buscar:
          <input
            type="text"
            placeholder="Unidad, chofer, aseguradora..."
            value={filtroGeneral}
            onChange={e => { setFiltroGeneral(e.target.value); setCurrentPage(1); }}
          />
        </label>
        <label>
          Inicio vigencia:
          <input
            type="date"
            value={filtroInicio}
            onChange={e => { setFiltroInicio(e.target.value); setCurrentPage(1); }}
          />
        </label>
        <label>
          Fin vigencia:
          <input
            type="date"
            value={filtroFin}
            onChange={e => { setFiltroFin(e.target.value); setCurrentPage(1); }}
          />
        </label>

        <button
          type="button"
          className="btn-limpiar-filtros"
          onClick={() => {
            setFiltroGeneral("");
            setFiltroInicio("");
            setFiltroFin("");
            setCurrentPage(1);
          }}
        >
          Limpiar filtros
        </button>

        <label>
          Mostrar:
          <select
            value={itemsPerPage}
            onChange={e => {
              const value = e.target.value === "Todos" ? garantiasFiltradas.length : Number(e.target.value);
              setItemsPerPage(value);
              setCurrentPage(1);
            }}
          >
            {itemsPerPageOptions.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        </label>

        <button onClick={() => setShowModal(true)} className="btn-registrar-garantia">
          Registrar Póliza
        </button>
      </div>

      {/* Tabla de garantías */}
      <div className="table-wrapper">
        <table className="elegant-table">
          <thead>
  <tr>
    <th style={{ display: "none" }}>ID</th>
    <th>Unidad</th>
    <th className="col-chofer">Chofer</th>
    <th>Marca</th>
    <th>Vehículo</th>
    <th>Aseguradora</th>
    <th>Tipo de Póliza</th>
    <th>No. de Póliza</th>
    <th>Teléfono Fijo</th>        {/* Nueva columna */}
    <th>Teléfono Celular</th>     {/* Nueva columna */}
    <th>URL de Póliza</th>
    <th>Suma Asegurada</th>
    <th>Inicio Vigencia</th>
    <th>Vigencia</th>
    <th>Prima</th>
    <th>Acciones</th>
  </tr>
            </thead>
            <tbody>
              {currentGarantias.map(g => (
                <tr key={g.id_garantia}>
                  <td style={{ display: "none" }}>{g.id_garantia}</td>
                  <td>{g.id_unidad}</td>
                  <td className="col-chofer">{g.chofer_asignado}</td>
                  <td>{g.marca}</td>
                  <td>{g.vehiculo}</td>
                  <td>{g.aseguradora}</td>
                  <td>{g.tipo_garantia}</td>
                  <td>{g.no_poliza}</td>
                  <td>{g.telefono_fijo || "—"}</td>        {/* Nuevo */}
                  <td>
                    {g.telefono_celular ? (
                      <a 
                        href={`https://wa.me/${g.telefono_celular.replace(/\D/g, '')}`} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        title={`Enviar WhatsApp a ${g.telefono_celular}`}
                      >
                        <i className="fa-brands fa-whatsapp" style={{ color: '#25D366', fontSize: '1.2rem' }}></i>
                      </a>
                    ) : "—"}
                  </td>

                  <td>
                    {g.url_poliza ? (
                      <button className="btn btn-outline-danger btn-sm" onClick={() => setModalFile(`${BASE_URL}${g.url_poliza}`)}>Ver Póliza</button>
                    ) : "—"}
                  </td>
                  <td>${g.suma_asegurada?.toLocaleString()}</td>
                  <td>{g.inicio_vigencia}</td>
                  <td>{g.vigencia}</td>
                  <td>${g.prima?.toLocaleString()}</td>
                  <td>
                    <div className="actions-container">
                      <button onClick={() => { setGarantiaToEdit(g); setShowModal(true); }}>
                        <i className="fa-solid fa-pen-to-square icon-edit"></i>
                      </button>
                      <button onClick={() => handleDeleteGarantia(g.id_garantia)}>
                        <i className="fa-solid fa-trash icon-delete"></i>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>

        </table>
      </div>

      {/* Tarjetas móviles */}
      <div className="card-wrapper">
        {currentGarantias.map(g => (
          <div key={g.id_garantia} className="unidad-card">
            <h3>{g.tipo_garantia} ({g.aseguradora})</h3>
            <p><b>ID Garantía:</b> {g.id_garantia}</p>
            <p><b>ID Unidad:</b> {g.id_unidad}</p>
            <p><b>Número de Póliza:</b> {g.no_poliza}</p>
            <p><b>URL Póliza:</b> 
              {g.url_poliza ? (
                <button onClick={() => setModalFile(`${BASE_URL}${g.url_poliza}`)}>Ver Póliza</button>
              ) : "—"}
            </p>
            <p><b>Suma Asegurada:</b> ${g.suma_asegurada}</p>
            <p><b>Inicio Vigencia:</b> {new Date(g.inicio_vigencia).toLocaleDateString()}</p>
            <p><b>Vigencia:</b> {new Date(g.vigencia).toLocaleDateString()}</p>
            <p><b>Prima:</b> ${g.prima}</p>
            <p><b>Teléfono Fijo:</b> {g.telefono_fijo || "—"}</p>
              <p>
                <b>WhatsApp:</b> 
                {g.telefono_celular ? (
                  <a 
                    href={`https://wa.me/${g.telefono_celular.replace(/\D/g, '')}`} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    title={`Enviar WhatsApp a ${g.telefono_celular}`}
                  >
                    <i className="fa-brands fa-whatsapp" style={{ color: '#25D366', fontSize: '1.5rem' }}></i>
                  </a>
                ) : "—"}
              </p>


            <div className="actions-container">
              <button onClick={() => { setGarantiaToEdit(g); setShowModal(true); }}>
                <i className="fa-solid fa-pen-to-square icon-edit"></i>
              </button>
              <button onClick={() => handleDeleteGarantia(g.id_garantia)}>
                <i className="fa-solid fa-trash icon-delete"></i>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Paginación */}
      <div className="pagination">
        <button onClick={() => setCurrentPage(p => Math.max(p - 1, 1))} disabled={currentPage === 1}>
          <i className="fa-solid fa-arrow-left"></i>
        </button>
        <span>Página {currentPage} de {totalPages}</span>
        <button onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))} disabled={currentPage === totalPages}>
          <i className="fa-solid fa-arrow-right"></i>
        </button>
      </div>

      {/* Modales */}
      {modalFile && <ModalFile url={modalFile} onClose={() => setModalFile(null)} />}
      {showModal && (
        <Crudgarantias
          onClose={() => { setShowModal(false); setGarantiaToEdit(null); }}
          onCreate={agregarOActualizarGarantia} 
          garantia={garantiaToEdit} 
        />
      )}
    </div>
  );
};

export default Garantias;
