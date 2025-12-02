import React, { useEffect, useState } from 'react';
import Modal from '../components/Modal';
import Select from 'react-select';
import { API_URL } from "../config";
import Swal from 'sweetalert2';
import './Garantias.css';

const Crudgarantias = ({ onClose, onCreate, garantia }) => {
  const [unidades, setUnidades] = useState([]);
  const [unidadSeleccionada, setUnidadSeleccionada] = useState(null);
  const [verificacion, setVerificacion] = useState(null); 
  const [formData, setFormData] = useState({
    aseguradora: '',
    tipo_garantia: '',
    no_poliza: '',
    suma_asegurada: '',
    inicio_vigencia: '',
    vigencia: '',
    prima: '',
    anos_vigencia: 1,
    telefono_fijo: '',       // nuevo
    telefono_celular: ''     // nuevo
  });
  const [archivo, setArchivo] = useState(null);

  // Traer unidades
  useEffect(() => {
    fetch(`${API_URL}/unidades`)
      .then(res => res.json())
      .then(data => setUnidades(data))
      .catch(err => console.error(err));
  }, []);

  // Si hay garantía para editar
  useEffect(() => {
    if (garantia) {
      setUnidadSeleccionada({ value: garantia.id_unidad, label: `ID: ${garantia.id_unidad} | ${garantia.vehiculo} - ${garantia.marca}` });
      const inicio = new Date(garantia.inicio_vigencia);
      const vig = new Date(garantia.vigencia);
      const diffYears = vig.getFullYear() - inicio.getFullYear();
      setFormData({
        aseguradora: garantia.aseguradora,
        tipo_garantia: garantia.tipo_garantia,
        no_poliza: garantia.no_poliza,
        suma_asegurada: garantia.suma_asegurada,
        inicio_vigencia: garantia.inicio_vigencia,
        vigencia: garantia.vigencia,
        prima: garantia.prima,
        anos_vigencia: diffYears || 1,
        telefono_fijo: garantia.telefono_fijo || '',
        telefono_celular: garantia.telefono_celular || ''
      });
      setVerificacion({ puede_renovar: true });
    }
  }, [garantia]);

  const handleUnidadChange = (option) => {
    setUnidadSeleccionada(option);
    setVerificacion(null);
    setFormData(prev => ({
      ...prev,
      aseguradora: '',
      tipo_garantia: '',
      no_poliza: '',
      suma_asegurada: '',
      inicio_vigencia: '',
      vigencia: '',
      prima: '',
      anos_vigencia: 1,
      telefono_fijo: '',
      telefono_celular: ''
    }));
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    // Calcular vigencia automática
    if (name === "inicio_vigencia" || name === "anos_vigencia") {
      const inicio = new Date(name === "inicio_vigencia" ? value : formData.inicio_vigencia);
      const anos = name === "anos_vigencia" ? parseInt(value) : parseInt(formData.anos_vigencia);
      if (inicio && anos > 0) {
        const nuevaVigencia = new Date(inicio);
        nuevaVigencia.setFullYear(nuevaVigencia.getFullYear() + anos);
        setFormData(prev => ({ ...prev, vigencia: nuevaVigencia.toISOString().split('T')[0] }));
      }
    }
  };

  const handleFileChange = (e) => setArchivo(e.target.files[0]);

  const verificarGarantia = async () => {
    if (!unidadSeleccionada) return alert('Selecciona una unidad');
    try {
      const res = await fetch(`${API_URL}/garantias/verificar/${unidadSeleccionada.value}`);
      const data = await res.json();
      setVerificacion(data);

      if (data.existe) {
        const vigencia = new Date(data.datos.vigencia);
        const hoy = new Date();
        const diasRestantes = Math.ceil((vigencia - hoy) / (1000 * 60 * 60 * 24));

        if (data.puede_renovar) {
          Swal.fire({
            title: '¡Listo para registrar!',
            text: 'Ya es tiempo de registrar o renovar la Poliza.',
            icon: 'success',
            confirmButtonColor: '#0d6efd',
            confirmButtonText: 'Aceptar',
            customClass: { popup: 'swal2-popup-over-modal' }
          });
        } else {
          Swal.fire({
            title: 'Poliza vigente',
            html: `No se puede registrar una nueva Poliza todavía.<br>
                   Vigencia: ${vigencia.toLocaleDateString()}<br>
                   Restan <b>${diasRestantes}</b> días.`,
            icon: 'info',
            confirmButtonColor: '#0d6efd',
            customClass: { popup: 'swal2-popup-over-modal' }
          });
        }

        // Rellenar datos previos
        if (data.datos) setFormData(prev => ({ ...prev, ...data.datos }));
      }

    } catch (err) {
      console.error(err);
      Swal.fire({
        title: 'Error',
        text: 'Error al verificar la Poliza',
        icon: 'error',
        confirmButtonColor: '#d33',
        customClass: { popup: 'swal2-popup-over-modal' }
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!unidadSeleccionada) return alert('Selecciona una unidad');

    const data = new FormData();
    data.append('id_unidad', unidadSeleccionada.value);
    for (let key in formData) data.append(key, formData[key]);
    if (archivo) data.append('archivo', archivo);

    const isUpdate = !!garantia;
    const url = isUpdate 
      ? `${API_URL}/api/garantias/${garantia.id_garantia}` 
      : `${API_URL}/api/garantias`;
    const method = isUpdate ? 'PUT' : 'POST';

    try {
      const res = await fetch(url, { method, body: data });
      const result = await res.json();

      if (res.ok) {
        onCreate({ id_unidad: unidadSeleccionada.value, ...formData, ...result });
        onClose();
      } else {
        Swal.fire({
          title: 'Error',
          text: result.error || 'Error al procesar la garantía',
          icon: 'error',
          confirmButtonColor: '#d33',
          customClass: { popup: 'swal2-popup-over-modal' }
        });
      }

    } catch (err) {
      console.error(err);
      Swal.fire({
        title: 'Error',
        text: 'Error al enviar la Poliza',
        icon: 'error',
        confirmButtonColor: '#d33',
        customClass: { popup: 'swal2-popup-over-modal' }
      });
    }
  };

  const unidadOptions = unidades.map(u => ({ 
    value: u.id_unidad, 
    label: `ID: ${u.id_unidad} | ${u.vehiculo} - ${u.marca} ${u.modelo}` 
  }));

  return (
    <Modal onClose={onClose}>
      <h2>{garantia ? 'Editar Poliza' : 'Registrar / Renovar Poliza'}</h2>

      {!garantia && (
        <div style={{ marginBottom: '1rem' }}>
          <Select
              options={unidadOptions}
              value={unidadSeleccionada}
              onChange={handleUnidadChange}
              placeholder="Selecciona una unidad..."
              isSearchable
              menuPortalTarget={document.body}    // renderiza el dropdown en body
              menuPosition="fixed"                // posición fija para que siga al scroll
              styles={{
                menuPortal: base => ({ ...base, zIndex: 9999 })  // asegurar que quede encima
              }}
            />

          <button type="button" onClick={verificarGarantia} style={{ marginTop: '0.5rem' }}>
            Verificar Poliza
          </button>
        </div>
      )}

      {verificacion && verificacion.existe && !verificacion.puede_renovar && (
        <p style={{ color: 'red' }}>La Poliza aún está vigente y no puede registrarse nueva.</p>
      )}

      {(verificacion && (!verificacion.existe || verificacion.puede_renovar)) || garantia ? (
        <form onSubmit={handleSubmit} className="modal-form">
          <input name="aseguradora" placeholder="Aseguradora" value={formData.aseguradora} onChange={handleChange} required />
          <input name="tipo_garantia" placeholder="Tipo Garantía" value={formData.tipo_garantia} onChange={handleChange} required />
          <input name="no_poliza" placeholder="Número Póliza" value={formData.no_poliza} onChange={handleChange} required />
          <input type="number" name="suma_asegurada" placeholder="Suma Asegurada" value={formData.suma_asegurada} onChange={handleChange} required />
          <input type="date" name="inicio_vigencia" value={formData.inicio_vigencia} onChange={handleChange} required />
          <input type="number" name="anos_vigencia" value={formData.anos_vigencia} min={1} onChange={handleChange} />
          <input type="date" name="vigencia" value={formData.vigencia} readOnly />
          <input type="number" name="prima" placeholder="Prima" value={formData.prima} onChange={handleChange} required />

          {/* Nuevos campos de teléfono */}
          <input name="telefono_fijo" placeholder="Teléfono fijo" value={formData.telefono_fijo} onChange={handleChange} />
          <input name="telefono_celular" placeholder="Teléfono celular" value={formData.telefono_celular} onChange={handleChange} />

          <input type="file" onChange={handleFileChange} accept=".pdf,.jpg,.png" />

          <div className="modal-actions">
            <button type="submit" className="btn-guardar">{garantia ? 'Actualizar Garantía' : 'Registrar Garantía'}</button>
          </div>
        </form>
      ) : null}
    </Modal>
  );
};

export default Crudgarantias;
