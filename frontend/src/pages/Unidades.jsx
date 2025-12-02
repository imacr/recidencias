// Unidades.jsx
import React, { useEffect, useState } from 'react';
import Swal from "sweetalert2";
import withReactContent from "sweetalert2-react-content";
import Modal from '../components/Modal'; // Ajusta la ruta según tu estructura
import '../../src/App.css';
import './Unidades.css';
import seces from '../assets/image.png';
import { BASE_URL } from "../config"; // Ajusta la ruta según la ubicación del archivo

const Unidades = () => {
  const [unidades, setUnidades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modalData, setModalData] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [unidadToEdit, setUnidadToEdit] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPageOptions = [5, 10, 20];
  const [itemsPerPage, setItemsPerPage] = useState(5);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const MySwal = withReactContent(Swal);
  const [pdfFrontal, setPdfFrontal] = useState(null);
  const [pdfTrasero, setPdfTrasero] = useState(null);
  const [agregarPlacas, setAgregarPlacas] = useState(false);
  const [fotoUnidad, setFotoUnidad] = useState(null);
  const [pdfFactura, setPdfFactura] = useState(null);
  const [empresas, setEmpresas] = useState([]);
  const [sucursales, setSucursales] = useState([]);
  const [sucursalesFiltradas, setSucursalesFiltradas] = useState([]);
  const [empresaSeleccionada, setEmpresaSeleccionada] = useState('');
  const [sucursalSeleccionada, setSucursalSeleccionada] = useState('');
  const [comprobantePago, setComprobantePago] = useState(null);
  const [tarjetaCirculacion, setTarjetaCirculacion] = useState(null);



  const API_URL = `${BASE_URL}/api/unidades`;

const [archivos, setArchivos] = useState({});

const handleChangeArchivo = (e) => {
  setArchivos({
    ...archivos,
    [e.target.name]: e.target.files[0]  // guarda solo un archivo por input
  });
};

useEffect(() => {
  // Cargar empresas
  fetch(`${BASE_URL}/empresas`)
    .then(res => res.json())
    .then(data => setEmpresas(data))
    .catch(err => console.error(err));

  // Cargar todas las sucursales (luego filtraremos)
  
}, []);

useEffect(() => {
  if (!empresaSeleccionada) return setSucursales([]);

  fetch(`${BASE_URL}/sucursales?empresa=${empresaSeleccionada}`)
    .then(res => res.json())
    .then(data => setSucursales(data))
    .catch(err => console.error(err));
}, [empresaSeleccionada]);

//----------------------------------------------------------------------------------
const [nuevaUnidad, setNuevaUnidad] = useState({
  id_empresa: "",
  sucursal: "",
  marca: "",
  vehiculo: "",
  modelo: "",
  clase_tipo: "",
  niv: "",
  motor: "",
  transmision: "",
  combustible: "",
  color: "",
  telefono_gps: "",
  sim_gps: "",
  uid: "",
  propietario: "",
  compra_arrendado: "",
  fecha_adquisicion: "",
  folio: "",
  placa: "",
  fecha_expedicion: "",
  fecha_vigencia: "",
  monto_pago: "",
});


//----------------------------------------------------------------------------------
// Obtener unidades
  useEffect(() => {
    const fetchUnidades = async () => {
      try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error('Error al obtener datos');
        const data = await response.json();
        setUnidades(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchUnidades();
  }, []);

  if (loading) return <div className="mensaje-estado">Cargando...</div>;
  if (error) return <div className="mensaje-estado error">{error}</div>;

  const indexOfLast = currentPage * itemsPerPage;
  const indexOfFirst = indexOfLast - itemsPerPage;
  const currentUnidades = unidades.slice(indexOfFirst, indexOfLast);
  const totalPages = Math.ceil(unidades.length / itemsPerPage);
  

  

  const toggleModal = () => setShowModal(!showModal);
    const handleChange = (e) => {
        const { name, value } = e.target;
        setUnidadToEdit(prev => ({ ...prev, [name]: value }));
    };

//----------------------------------------------------------------------------------
//manejar cambios en nueva unidad

const handleChangeNuevaUnidad = (e) => {
  const { name, value } = e.target;
  setNuevaUnidad(prev => ({ ...prev, [name]: value }));
};



//----------------------------------------------------------------------------------
// Actualizar unidad
const handleUpdateUnidad = async (e) => {
  e.preventDefault();

  try {
    const formData = new FormData();

    // ----------------------------
    // Campos directos de unidadToEdit
    // ----------------------------
    const camposDirectos = [
      "marca", "vehiculo", "modelo", "fecha_adquisicion",
      "valor_factura", "kilometraje_actual", "id_empresa", "sucursal",
      "niv"  
    ];

    camposDirectos.forEach(field => {
      let valor = unidadToEdit[field];
      formData.append(field, valor !== undefined && valor !== null ? valor.toString() : "");
    });

    // ----------------------------
    // Campos dentro de mas_datos
    // ----------------------------
    const camposMasDatos = [
      "clase_tipo", "motor", "transmision", "combustible", 
      "color", "propietario", "compra_arrendado", 
      "telefono_gps", "sim_gps", "uid"
    ];

    camposMasDatos.forEach(field => {
      let valor = unidadToEdit.mas_datos?.[field];
      formData.append(field, valor !== undefined && valor !== null ? valor.toString() : "");
    });

    // ----------------------------
    // Archivos opcionales
    // ----------------------------
    if (fotoUnidad) formData.append("foto_unidad", fotoUnidad);
    if (pdfFactura) formData.append("pdf_factura", pdfFactura);
    if (pdfFrontal) formData.append("pdf_frontal", pdfFrontal);
    if (pdfTrasero) formData.append("pdf_trasero", pdfTrasero);

    // ----------------------------
    // Debug: revisar datos antes de enviar
    // ----------------------------
    console.log("=== FormData a enviar ===");
    for (let pair of formData.entries()) {
      console.log(pair[0], ":", pair[1]);
    }

    // ----------------------------
    // Petición PUT al backend
    // ----------------------------
    const response = await fetch(`${API_URL}/${unidadToEdit.id_unidad}`, {
      method: "PUT",
      body: formData
    });

    if (!response.ok) {
      const errorResponse = await response.json();
      throw new Error(errorResponse.error || "Error al actualizar unidad");
    }

    const data = await response.json();
    console.log("Unidad actualizada:", data);

    // ----------------------------
    // Refrescar lista y cerrar modal
    // ----------------------------
    const unidadesActualizadas = await fetch(API_URL).then(r => r.json());
    setUnidades(unidadesActualizadas);
    setShowModal(false);
    setUnidadToEdit(null);

    Swal.fire({
      title: "¡Éxito!",
      text: "Unidad actualizada correctamente",
      icon: "success",
      confirmButtonColor: "#28a745",
    });

  } catch (err) {
    console.error(err);
    Swal.fire({
      title: "Error",
      text: err.message,
      icon: "error",
      confirmButtonColor: "#d33",
    });
  }
};

//----------------------------------------------------------------------------------
// Eliminar unidad

const handleDeleteUnidad = async (id_unidad) => {
  const result = await Swal.fire({
    title: '¿Estás seguro?',
    text: "Esta acción eliminará la unidad permanentemente.",
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#d33',  // rojo
    cancelButtonColor: '#3085d6', // azul
    confirmButtonText: 'Sí, eliminar',
    cancelButtonText: 'Cancelar'
  });

  if (!result.isConfirmed) return; // <- Si el usuario cancela, NO se elimina

  try {
    const response = await fetch(`${API_URL}/${id_unidad}`, {
      method: 'DELETE',
    });

    if (!response.ok) throw new Error('Error al eliminar la unidad');

    // Refrescar lista
    const data = await fetch(API_URL).then(r => r.json());
    setUnidades(data);

    Swal.fire({
      title: '¡Éxito!',
      text: 'Unidad eliminada correctamente',
      icon: 'success',
      iconColor: '#ca0808ff',
      confirmButtonColor: '#28a745'
    });

  } catch (err) {
    Swal.fire({
      title: 'Error',
      text: err.message,
      icon: 'error',
      confirmButtonColor: '#d33'
    });
  }
};

//----------------------------------------------------------------------------------
// Agregar nueva unidad
const handleAgregarUnidad = async (e) => {
  e.preventDefault();

  try {
    // Validaciones básicas
    if (!nuevaUnidad.id_empresa) throw new Error("Seleccione una empresa");
    if (!nuevaUnidad.sucursal) throw new Error("Seleccione una sucursal");

    const formData = new FormData();

    // Agregar campos de texto excepto id_empresa e id_sucursal
    for (const key in nuevaUnidad) {
      if (nuevaUnidad[key] !== null && nuevaUnidad[key] !== "" && key !== "id_empresa" && key !== "sucursal") {
        formData.append(key, nuevaUnidad[key]);
      }
    }

    // Agregar id_empresa e id_sucursal como números
    formData.append("empresa", parseInt(nuevaUnidad.id_empresa));
    formData.append("sucursal", parseInt(nuevaUnidad.sucursal));

    // Archivos opcionales
    if (fotoUnidad) formData.append("foto_unidad", fotoUnidad);
    if (pdfFactura) formData.append("pdf_factura", pdfFactura);
    if (agregarPlacas) {
    if (nuevaUnidad.placa) formData.append("placa", nuevaUnidad.placa);
    if (nuevaUnidad.folio) formData.append("folio", nuevaUnidad.folio);
    if (nuevaUnidad.fecha_expedicion) formData.append("fecha_expedicion", nuevaUnidad.fecha_expedicion);
    if (nuevaUnidad.fecha_vigencia) formData.append("fecha_vigencia", nuevaUnidad.fecha_vigencia);
    if (pdfFrontal) formData.append("pdf_frontal", pdfFrontal);
    if (pdfTrasero) formData.append("pdf_trasero", pdfTrasero);
    if (comprobantePago) formData.append("comprobante", comprobantePago);
    if (tarjetaCirculacion) formData.append("tarjeta_circulacion", tarjetaCirculacion);

    }

    // Enviar a la API
    const response = await fetch(`${API_URL}`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorRes = await response.json();
      console.error("Error API:", errorRes);
      throw new Error(errorRes.message || "Error al agregar unidad");
    }

    const data = await response.json();

    // Éxito
    setUnidades(prev => [...prev, data]);
    Swal.fire({
      title: "¡Éxito!",
      text: "Unidad agregada correctamente",
      icon: "success",
      confirmButtonColor: "#28a745",
    });

    // Limpiar estado
    setNuevaUnidad({
      id_empresa: "",
      sucursal: "",
      marca: "",
      vehiculo: "",
      modelo: "",
      clase_tipo: "",
      niv: "",
      motor: "",
      transmision: "",
      combustible: "",
      color: "",
      telefono_gps: "",
      sim_gps: "",
      uid: "",
      propietario: "",
      compra_arrendado: "",
      fecha_adquisicion: "",
      folio: "",
      placa: "",
      fecha_expedicion: "",
      fecha_vigencia: "",
      valor_factura: "",
      kilometraje_actual: ""
    });
    setFotoUnidad(null);
    setPdfFactura(null);
    setPdfFrontal(null);
    setPdfTrasero(null);
    setAgregarPlacas(false);
    setShowModal(false);

  } catch (err) {
    Swal.fire({
      title: "Error",
      text: err.message,
      icon: "error",
      confirmButtonColor: "#d33"
    });
  }
};



  return (
    <div className="unidades-container">
      <h1><i className="fa-solid fa-car-side"></i> Unidades</h1>

      <div className="pagination-controls">
          <label className='pagination-label'>
            Mostrar:
            <select className="pagination-select"
              value={itemsPerPage}
              onChange={e => {
                setItemsPerPage(Number(e.target.value));
                setCurrentPage(1);
              }}
            >
              {itemsPerPageOptions.map(opt => (
                <option className='' key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </label>
        <button  className="btn-open-modal btn-registrar-garantia" onClick={() => { setShowModal(true);
            setUnidadToEdit(null);  // Para abrir en modo "Agregar"
            setNuevaUnidad({});     // Inicializa campos vacíos para agregar
            setModalData(null);     // Limpia detalles
          }} >
          Agregar Nueva Unidad
        </button>
      </div>

      {/* Tabla para pantallas grandes */}
      <div className="table-wrapper">
        <table className="elegant-table">
          <thead>
            <tr>
              <th textAlign="center">ID</th>
              <th>Chofer Asignado</th>
              <th>Marca</th>
              <th>Vehículo</th>
              <th>Modelo</th>
              <th >NIV</th>
              <th>Placa</th>
              <th>Fecha Adquisición</th>
              <th>Vencimiento Tarjeta</th>
              <th>Estado</th>
              <th>Engomado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {currentUnidades.map(u => (
              <tr key={u.id_unidad}>
                <td>{u.id_unidad}</td>
                <td>{u.chofer_asignado}</td>
                <td>{u.marca}</td>
                <td>{u.vehiculo}</td>
                <td>{u.modelo}</td>
                <td>{u.niv}</td>
                <td>{u.placa}</td>
                <td>{u.fecha_adquisicion}</td>
                <td>{u.fecha_vencimiento_tarjeta}</td>
                <td>{u.estado_tarjeta}</td>
                <td>{u.engomado}</td>
                <td>
                   <div className="actions-container">
                    {/* ACTUALIZAR (Verde) */}
                    <button onClick={() => { setUnidadToEdit(u); setShowModal(true); }}>
                    <i className="fa-solid fa-pen-to-square icon-edit"></i>
                    </button>

                    {/* ELIMINAR (Rojo) */}
                    <button onClick={() => handleDeleteUnidad(u.id_unidad)}>
                      <i className="fa-solid fa-trash icon-delete"></i>
                    </button>

                    {/* DETALLES/MÁS DATOS (Azul) */}
                    <button onClick={() => { setModalData(u.mas_datos); setShowModal(true); }}>
                    {/* Usé 'icon-details' para la acción de ver más */}
                    <i className="fa-solid fa-plus-minus icon-details"></i>
                    </button>
                </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Tarjetas para pantallas pequeñas */}
      <div className="card-wrapper">
        {currentUnidades.map(u => (
          <div key={u.id_unidad} className="unidad-card">
            <h3>{u.vehiculo} ({u.marca})</h3>
            <p><b>ID:</b> {u.id_unidad}</p>
            <p><b>Modelo:</b> {u.modelo}</p>
            <p><b>NIV:</b> {u.niv}</p>
            <p><b>Placa:</b> {u.placa}</p>
            <p><b>Fecha Adquisición:</b> {u.fecha_adquisicion}</p>
            <p><b>Vencimiento Tarjeta:</b> {u.fecha_vencimiento_tarjeta}</p>
            <p><b>Estado:</b> {u.estado_tarjeta}</p>
            <p><b>Engomado:</b> {u.engomado}</p>
            <p><b>Chofer:</b> {u.chofer_asignado}</p>
            <div className="actions-container">
                     {/* ACTUALIZAR (Verde) */}
                    <button onClick={() => { setUnidadToEdit(u); setShowModal(true); }}>
                    <i className="fa-solid fa-pen-to-square icon-edit"></i>
                    </button>

                    {/* ELIMINAR (Rojo) */}
                    <button onClick={() => handleDeleteUnidad(u.id_unidad)}>
                      <i className="fa-solid fa-trash icon-delete"></i>
                    </button>


                    {/* DETALLES/MÁS DATOS (Azul) */}
                    <button onClick={() => { setModalData(u.mas_datos); setShowModal(true); }}>
                    {/* Usé 'icon-details' para la acción de ver más */}
                    <i className="fa-solid fa-plus-minus icon-details"></i>
                    </button>
                </div>
          </div>
        ))}
      </div>

      {/* Paginación */}
      <div className="pagination">
        <button onClick={() => setCurrentPage(p => Math.max(p - 1, 1))} disabled={currentPage === 1}><i class="fa-solid fa-arrow-left"></i></button>
        <span>Página {currentPage} de {totalPages}</span>
        <button onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))} disabled={currentPage === totalPages}><i class="fa-solid fa-arrow-right"></i></button>
      </div>



  {showModal && (
    <div className='modal-container'>
    <Modal onClose={() => { setShowModal(false); setUnidadToEdit(null); setNuevaUnidad(null); }}>
        {unidadToEdit ? (
          <>
            <h2 style={{ textAlign: 'center' }}>Editar Unidad</h2>

      <form onSubmit={handleUpdateUnidad} className="form-container">

  {/* ----------------------------- */}
  {/* SELECCIÓN DE EMPRESA Y SUCURSAL */}
  {/* ----------------------------- */}
  <h4>Empresa y Sucursal</h4>
<div className="form-group">
  <label>Empresa</label>
  <select
    value={unidadToEdit.id_empresa || ""}
    onChange={e => {
      const empresaId = e.target.value;
      setUnidadToEdit(prev => ({ ...prev, id_empresa: empresaId, sucursal: "" })); // resetear sucursal
      setEmpresaSeleccionada(empresaId); // activa filtrado de sucursales
    }}
  >
    <option value="">Seleccione una empresa</option>
    {empresas.map(e => (
      <option key={e.id_empresa} value={e.id_empresa}>
        {e.razon_social}
      </option>
    ))}
  </select>
</div>

<div className="form-group">
  <label>Sucursal</label>
  <select
    value={unidadToEdit.sucursal || ""}
    onChange={e => setUnidadToEdit(prev => ({ ...prev, sucursal: e.target.value }))}
    disabled={!empresaSeleccionada} // deshabilitado si no hay empresa seleccionada
  >
    <option value="">Seleccione una sucursal</option>
    {sucursales.map(s => (
      <option key={s.id_sucursal} value={s.id_sucursal}>
        {s.nombre}
      </option>
    ))}
  </select>
</div>

  {/* ----------------------------- */}
  {/* DATOS DEL VEHÍCULO */}
  {/* ----------------------------- */}
  <h4>Datos del Vehículo</h4>
  <div className="form-row">
    <div className="form-group">
      <label>Marca</label>
      <input type="text" name="marca" value={unidadToEdit.marca || ""} onChange={e => setUnidadToEdit({...unidadToEdit, marca: e.target.value})} required />
    </div>
    <div className="form-group">
      <label>Vehículo</label>
      <input type="text" name="vehiculo" value={unidadToEdit.vehiculo || ""} onChange={e => setUnidadToEdit({...unidadToEdit, vehiculo: e.target.value})} required />
    </div>
    <div className="form-group">
      <label>Modelo</label>
      <input type="number" name="modelo" value={unidadToEdit.modelo || ""} onChange={e => setUnidadToEdit({...unidadToEdit, modelo: e.target.value})} required />
    </div>
  </div>

  <div className="form-row">
    <div className="form-group">
      <label>Clase Tipo</label>
      <input type="text" value={unidadToEdit.mas_datos?.clase_tipo || ""} onChange={e => setUnidadToEdit({...unidadToEdit, mas_datos: {...unidadToEdit.mas_datos, clase_tipo: e.target.value}})} />
    </div>
    <div className="form-group">
      <label>NIV</label>
        <input type="text" value={unidadToEdit.niv || ""} onChange={e => setUnidadToEdit({...unidadToEdit, niv: e.target.value})} />
    </div>
    <div className="form-group">
      <label>Motor</label>
      <input type="text" value={unidadToEdit.mas_datos?.motor || ""} onChange={e => setUnidadToEdit({...unidadToEdit, mas_datos: {...unidadToEdit.mas_datos, motor: e.target.value}})} />
    </div>
  </div>

  <div className="form-row">
    <div className="form-group">
      <label>Transmisión</label>
      <select value={unidadToEdit.mas_datos?.transmision || ""} onChange={e => setUnidadToEdit({...unidadToEdit, mas_datos: {...unidadToEdit.mas_datos, transmision: e.target.value}})}>
        <option value="">Seleccione</option>
        <option value="Automática">Automática</option>
        <option value="Manual">Manual</option>
        <option value="CVT">CVT</option>
      </select>
    </div>
    <div className="form-group">
      <label>Combustible</label>
      <select value={unidadToEdit.mas_datos?.combustible || ""} onChange={e => setUnidadToEdit({...unidadToEdit, mas_datos: {...unidadToEdit.mas_datos, combustible: e.target.value}})}>
        <option value="">Seleccione</option>
        <option value="Gasolina">Gasolina</option>
        <option value="Diésel">Diésel</option>
        <option value="Eléctrico">Eléctrico</option>
        <option value="Híbrido">Híbrido</option>
      </select>
    </div>
    <div className="form-group">
      <label>Color</label>
      <input type="text" value={unidadToEdit.mas_datos?.color || ""} onChange={e => setUnidadToEdit({...unidadToEdit, mas_datos: {...unidadToEdit.mas_datos, color: e.target.value}})} />
    </div>
  </div>

  <div className="form-row">
    <div className="form-group">
      <label>Fecha Adquisición</label>
      <input type="date" value={unidadToEdit.fecha_adquisicion || ""} onChange={e => setUnidadToEdit({...unidadToEdit, fecha_adquisicion: e.target.value})} />
    </div>
    <div className="form-group">
      <label>Propietario</label>
      <input type="text" value={unidadToEdit.mas_datos?.propietario || ""} onChange={e => setUnidadToEdit({...unidadToEdit, mas_datos: {...unidadToEdit.mas_datos, propietario: e.target.value}})} />
    </div>
    <div className="form-group">
      <label>Compra o Arrendado</label>
      <input type="text" value={unidadToEdit.mas_datos?.compra_arrendado || ""} onChange={e => setUnidadToEdit({...unidadToEdit, mas_datos: {...unidadToEdit.mas_datos, compra_arrendado: e.target.value}})} />
    </div>
  </div>

  {/* DOCUMENTOS Y VALORES */}
  <div className="form-row">
    <div className="form-group">
      <label>Foto de la Unidad</label>
      <input type="file" accept="image/*" onChange={(e) => setFotoUnidad(e.target.files[0])} />
    </div>
    <div className="form-group">
      <label>Factura (PDF)</label>
      <input type="file" accept="application/pdf" onChange={(e) => setPdfFactura(e.target.files[0])} />
    </div>
    <div className="form-group">
      <label>Valor Factura</label>
      <input type="number" step="0.01" value={unidadToEdit.valor_factura || ""} onChange={e => setUnidadToEdit({...unidadToEdit, valor_factura: e.target.value})} />
    </div>
  </div>

  <div className="form-row">
    <div className="form-group">
      <label>Kilometraje actual</label>
      <input type="number" value={unidadToEdit.kilometraje_actual || ""} onChange={e => setUnidadToEdit({...unidadToEdit, kilometraje_actual: e.target.value})} />
    </div>
  </div>

  {/* GPS */}
  <h4>Datos de Navegación (GPS)</h4>
  <div className="form-row">
    <div className="form-group">
      <label>Teléfono GPS</label>
      <input type="text" value={unidadToEdit.mas_datos?.telefono_gps || ""} onChange={e => setUnidadToEdit({...unidadToEdit, mas_datos: {...unidadToEdit.mas_datos, telefono_gps: e.target.value}})} />
    </div>
    <div className="form-group">
      <label>SIM GPS</label>
      <input type="text" value={unidadToEdit.mas_datos?.sim_gps || ""} onChange={e => setUnidadToEdit({...unidadToEdit, mas_datos: {...unidadToEdit.mas_datos, sim_gps: e.target.value}})} />
    </div>
    <div className="form-group">
      <label>UID</label>
      <input type="text" value={unidadToEdit.mas_datos?.uid || ""} onChange={e => setUnidadToEdit({...unidadToEdit, mas_datos: {...unidadToEdit.mas_datos, uid: e.target.value}})} />
    </div>
  </div>

  <button type="submit" className="btn-save">Guardar Cambios</button>
</form>


          </>
        ) : nuevaUnidad ? (
        <><h2 style={{ textAlign: 'center' }}>Agregar Nueva Unidad con Placa</h2>
    {/* =========================
        FORMULARIO (agregar unidad)
        ========================= */}

<form onSubmit={handleAgregarUnidad} className="form-container">

  {/* ----------------------------- */}
  {/* SELECCIÓN DE EMPRESA Y SUCURSAL */}
  {/* ----------------------------- */}
  <h4>Empresa y Sucursal</h4>
  <div className="form-group">
    <label>Empresa</label>
    <select
      value={nuevaUnidad.id_empresa || ""}
      onChange={e => {
        const empresaId = e.target.value;
        setNuevaUnidad(prev => ({ ...prev, id_empresa: empresaId, sucursal: "" }));
        setEmpresaSeleccionada(empresaId);
      }}
    >
      <option value="">Seleccione una empresa</option>
      {empresas.map(e => (
        <option key={e.id_empresa} value={e.id_empresa}>
          {e.razon_social}
        </option>
      ))}
    </select>
  </div>

  <div className="form-group">
    <label>Sucursal</label>
    <select
      value={nuevaUnidad.sucursal || ""}
      onChange={e => setNuevaUnidad(prev => ({ ...prev, sucursal: e.target.value }))}
      disabled={!empresaSeleccionada}
    >
      <option value="">Seleccione una sucursal</option>
      {sucursales.map(s => (
        <option key={s.id_sucursal} value={s.id_sucursal}>
          {s.nombre}
        </option>
      ))}
    </select>
  </div>

  {/* ----------------------------- */}
  {/* DATOS DEL VEHÍCULO */}
  {/* ----------------------------- */}
  <h4>Datos del Vehículo</h4>
  <div className="form-row">
    <div className="form-group">
      <label>Marca</label>
      <input type="text" name="marca" value={nuevaUnidad.marca || ""} onChange={handleChangeNuevaUnidad} required />
    </div>
    <div className="form-group">
      <label>Vehículo</label>
      <input type="text" name="vehiculo" value={nuevaUnidad.vehiculo || ""} onChange={handleChangeNuevaUnidad} required />
    </div>
    <div className="form-group">
      <label>Modelo</label>
      <input type="number" name="modelo" value={nuevaUnidad.modelo || ""} onChange={handleChangeNuevaUnidad} required />
    </div>
  </div>

  <div className="form-row">
    <div className="form-group">
      <label>Clase Tipo</label>
      <input type="text" name="clase_tipo" value={nuevaUnidad.clase_tipo || ""} onChange={handleChangeNuevaUnidad} />
    </div>
    <div className="form-group">
      <label>NIV</label>
      <input type="text" name="niv" value={nuevaUnidad.niv || ""} onChange={handleChangeNuevaUnidad} />
    </div>
    <div className="form-group">
      <label>Motor</label>
      <input type="text" name="motor" value={nuevaUnidad.motor || ""} onChange={handleChangeNuevaUnidad} />
    </div>
  </div>

  <div className="form-row">
    <div className="form-group">
      <label>Transmisión</label>
      <select name="transmision" value={nuevaUnidad.transmision || ""} onChange={handleChangeNuevaUnidad}>
        <option value="">Seleccione</option>
        <option value="Automática">Automática</option>
        <option value="Manual">Manual</option>
        <option value="CVT">CVT</option>
      </select>
    </div>
    <div className="form-group">
      <label>Combustible</label>
      <select name="combustible" value={nuevaUnidad.combustible || ""} onChange={handleChangeNuevaUnidad}>
        <option value="">Seleccione</option>
        <option value="Gasolina">Gasolina</option>
        <option value="Diésel">Diésel</option>
        <option value="Eléctrico">Eléctrico</option>
        <option value="Híbrido">Híbrido</option>
      </select>
    </div>
    <div className="form-group">
      <label>Color</label>
      <input type="text" name="color" value={nuevaUnidad.color || ""} onChange={handleChangeNuevaUnidad} />
    </div>
  </div>

  <div className="form-row">
    <div className="form-group">
      <label>Fecha Adquisición</label>
      <input type="date" name="fecha_adquisicion" value={nuevaUnidad.fecha_adquisicion || ""} onChange={handleChangeNuevaUnidad} />
    </div>
    <div className="form-group">
      <label>Propietario</label>
      <input type="text" name="propietario" value={nuevaUnidad.propietario || ""} onChange={handleChangeNuevaUnidad} />
    </div>
    <div className="form-group">
      <label>Compra o Arrendado</label>
      <input type="text" name="compra_arrendado" value={nuevaUnidad.compra_arrendado || ""} onChange={handleChangeNuevaUnidad} />
    </div>
  </div>

  {/* DOCUMENTOS Y VALORES */}
  <div className="form-row">
    <div className="form-group">
      <label>Foto de la Unidad</label>
      <input type="file" accept="image/*" onChange={(e) => setFotoUnidad(e.target.files[0])} />
    </div>
    <div className="form-group">
      <label>Factura (PDF)</label>
      <input type="file" accept="application/pdf" onChange={(e) => setPdfFactura(e.target.files[0])} />
    </div>
    <div className="form-group">
      <label>Valor Factura</label>
      <input type="number" step="0.01" name="valor_factura" value={nuevaUnidad.valor_factura || ""} onChange={handleChangeNuevaUnidad} />
    </div>
  </div>

  <div className="form-row">
    <div className="form-group">
      <label>Kilometraje actual</label>
      <input type="number" name="kilometraje_actual" value={nuevaUnidad.kilometraje_actual || ""} onChange={handleChangeNuevaUnidad} />
    </div>
  </div>

  {/* GPS */}
  <h4>Datos de Navegación (GPS)</h4>
  <div className="form-row">
    <div className="form-group">
      <label>Teléfono GPS</label>
      <input type="text" name="telefono_gps" value={nuevaUnidad.telefono_gps || ""} onChange={handleChangeNuevaUnidad} />
    </div>
    <div className="form-group">
      <label>SIM GPS</label>
      <input type="text" name="sim_gps" value={nuevaUnidad.sim_gps || ""} onChange={handleChangeNuevaUnidad} />
    </div>
    <div className="form-group">
      <label>UID</label>
      <input type="text" name="uid" value={nuevaUnidad.uid || ""} onChange={handleChangeNuevaUnidad} />
    </div>
  </div>

  {/* PLACAS (opcional) */}
  <h3>Placas (Opcional)</h3>
  <div className="form-group">
    <label>
      <input type="checkbox" checked={agregarPlacas} onChange={() => setAgregarPlacas(!agregarPlacas)} />
      &nbsp;Agregar placas
    </label>
  </div>

  {agregarPlacas && (
    <>
      <div className="form-row">
        <div className="form-group">
          <label>Placa</label>
          <input type="text" name="placa" value={nuevaUnidad.placa || ""} onChange={handleChangeNuevaUnidad} />
        </div>
        <div className="form-group">
          <label>Folio de la tarjeta de circulación</label>
          <input type="text" name="folio" value={nuevaUnidad.folio || ""} onChange={handleChangeNuevaUnidad} />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Fecha Expedición</label>
          <input type="date" name="fecha_expedicion" value={nuevaUnidad.fecha_expedicion || ""} onChange={handleChangeNuevaUnidad} />
        </div>
        <div className="form-group">
          <label>Fecha Vigencia</label>
          <input type="date" name="fecha_vigencia" value={nuevaUnidad.fecha_vigencia || ""} onChange={handleChangeNuevaUnidad} />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Monto Pago de las placas</label>
          <input type="number" name="monto_pago" value={nuevaUnidad.monto_pago || ""} onChange={handleChangeNuevaUnidad} />
        </div>
         <div className="form-group">
          <label>Comprobante del Pago (PDF)</label>
          <input type="file" accept="application/pdf" onChange={(e) => setComprobantePago(e.target.files[0])} />
        </div>
        <div className="form-group">
          <label>PDF Placa Frontal</label>
          <input type="file" accept="application/pdf" onChange={(e) => setPdfFrontal(e.target.files[0])} />
        </div>
      </div>

      <div className="form-row">
        
        <div className="form-group">
          <label>PDF Placa Trasera</label>
          <input type="file" accept="application/pdf" onChange={(e) => setPdfTrasero(e.target.files[0])} />
        </div>
       
        <div className="form-group">
          <label>Tarjeta de Circulación (PDF)</label>
          <input type="file" accept="application/pdf" onChange={(e) => setTarjetaCirculacion(e.target.files[0])} />
        </div>
      </div>
    </>
  )}

  <button type="submit" className="btn-save">Agregar Unidad</button>
</form>



       
          
        </>
      ) :(
          <>
             <h2 className="details-header">Detalles adicionales</h2> {/* Aplicar clase aquí */}
          <div className="details-container">
            {modalData ? (
              Object.entries(modalData).map(([key, value]) => (
                <div key={key} className="detail-item">
                  <strong>{key.replace(/_/g, ' ')}:</strong>
                  <span>{value ? value.toString() : 'N/A'}</span>
                </div>
              ))
            ) : (
              <p>No hay datos para mostrar.</p>
            )}
          </div>
          </>

        )}

        
      </Modal>
    </div>
  )}
   
    </div>
  );
};

export default Unidades;