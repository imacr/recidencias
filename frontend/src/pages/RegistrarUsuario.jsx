import React, { useEffect, useState } from "react";
import Modal from "../components/Modal";
import { BASE_URL } from "../config";
import Swal from "sweetalert2";
import './registro_usuario.css';

const initialFormData = {
  nombre: "",
  usuario: "",
  contraseña: "",
  correo: "",
  rol: "usuario",
  estado: "activo",
  chofer: null,
  crearChofer: false,
  curp: "",
  calle: "",
  colonia_localidad: "",
  codpos: "",
  municipio: "",
  licencia_folio: "",
  licencia_tipo: "",
  licencia_vigencia: ""
};

const RegistrarUsuario = ({ show, onClose, onCreate, usuarioToEdit }) => {
  const API_URL = `${BASE_URL}/api/usuarios`;

  const [formData, setFormData] = useState(initialFormData);
  const [choferesExistentes, setChoferesExistentes] = useState([]);

  // Cargar datos del usuario si es edición
  useEffect(() => {
    if (usuarioToEdit) {
      setFormData({
        nombre: usuarioToEdit.nombre || "",
        usuario: usuarioToEdit.usuario || "",
        contraseña: "", // No mostrar la contraseña
        correo: usuarioToEdit.correo || "",
        rol: usuarioToEdit.rol || "usuario",
        estado: usuarioToEdit.estado || "activo",
        chofer: usuarioToEdit.id_chofer || null,
        crearChofer: false,
        curp: usuarioToEdit.chofer?.curp || "",
        calle: usuarioToEdit.chofer?.calle || "",
        colonia_localidad: usuarioToEdit.chofer?.colonia_localidad || "",
        codpos: usuarioToEdit.chofer?.codpos || "",
        municipio: usuarioToEdit.chofer?.municipio || "",
        licencia_folio: usuarioToEdit.chofer?.licencia_folio || "",
        licencia_tipo: usuarioToEdit.chofer?.licencia_tipo || "",
        licencia_vigencia: usuarioToEdit.chofer?.licencia_vigencia || ""
      });
    } else {
      setFormData(initialFormData);
    }
  }, [usuarioToEdit]);

  // Cargar choferes existentes si el rol es chofer
  useEffect(() => {
    if (formData.rol === "chofer") {
      fetch(`${BASE_URL}/api/choferes`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
      })
        .then(res => res.json())
        .then(data => setChoferesExistentes(data))
        .catch(err => console.error(err));
    }
  }, [formData.rol]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value
    }));
  };

  const validarCamposChofer = () => {
    if (!formData.curp || !formData.licencia_folio || !formData.licencia_tipo || !formData.licencia_vigencia) {
      Swal.fire({
        title: 'Campos incompletos',
        text: 'Debes completar todos los campos obligatorios del chofer.',
        icon: 'warning',
        confirmButtonColor: '#ffc107'
      });
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.rol === "chofer" && formData.crearChofer && !validarCamposChofer()) return;

    // Preparar payload
    const payload = {
      nombre: formData.nombre,
      usuario: formData.usuario,
      correo: formData.correo,
      rol: formData.rol,
      estado: formData.estado
    };

    if (formData.contraseña) payload.contraseña = formData.contraseña;

    if (formData.rol === 'chofer') {
      if (formData.crearChofer) {
        payload.crear_chofer = true;
        payload.chofer_data = {
          nombre: formData.nombre,
          curp: formData.curp,
          calle: formData.calle,
          colonia_localidad: formData.colonia_localidad,
          codpos: formData.codpos,
          municipio: formData.municipio,
          licencia_folio: formData.licencia_folio,
          licencia_tipo: formData.licencia_tipo,
          licencia_vigencia: formData.licencia_vigencia
        };
      } else {
        payload.id_chofer = formData.chofer;
      }
    }

    try {
      const url = usuarioToEdit ? `${API_URL}/${usuarioToEdit.id_usuario}` : API_URL;
      const method = usuarioToEdit ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem("token")}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText);
      }

      const data = await response.json();
      onCreate(data); // Actualiza la tabla en el frontend
      onClose();
      if (!usuarioToEdit) setFormData(initialFormData);

      Swal.fire({
        title: '¡Éxito!',
        text: usuarioToEdit ? 'Usuario actualizado correctamente' : 'Usuario agregado correctamente',
        icon: 'success',
        confirmButtonColor: '#28a745'
      });

    } catch (err) {
      console.error(err);
      Swal.fire({
        title: 'Error',
        text: `No se pudo guardar el usuario: ${err.message}`,
        icon: 'error',
        confirmButtonColor: '#dc3545'
      });
    }
  };

  if (!show) return null;

  return (
    <Modal onClose={onClose}>
      <h2>{usuarioToEdit ? "Actualizar Usuario" : "Registrar Nuevo Usuario"}</h2>
      <form onSubmit={handleSubmit} className="modal-form">
        <input type="text" name="nombre" placeholder="Nombre completo" value={formData.nombre} onChange={handleChange} required />
        <input type="text" name="usuario" placeholder="Usuario" value={formData.usuario} onChange={handleChange} required />
        <input type="password" name="contraseña" placeholder={usuarioToEdit ? "Nueva contraseña (opcional)" : "Contraseña"} value={formData.contraseña} onChange={handleChange} />
        <input type="email" name="correo" placeholder="Correo electrónico" value={formData.correo} onChange={handleChange} required />

        <select name="rol" value={formData.rol} onChange={handleChange}>
          <option value="admin">Admin</option>
          <option value="usuario">Usuario</option>
          <option value="chofer">Chofer</option>
        </select>

        <select name="estado" value={formData.estado} onChange={handleChange}>
          <option value="activo">Activo</option>
          <option value="inactivo">Inactivo</option>
        </select>

        {formData.rol === "chofer" && (
          <>
            <label>
              <input type="checkbox" name="crearChofer" checked={formData.crearChofer} onChange={handleChange} />
              Crear nuevo chofer
            </label>

            {formData.crearChofer ? (
              <>
                <input type="text" name="curp" placeholder="CURP" value={formData.curp} onChange={handleChange} required />
                <input type="text" name="calle" placeholder="Calle" value={formData.calle} onChange={handleChange} />
                <input type="text" name="colonia_localidad" placeholder="Colonia/Localidad" value={formData.colonia_localidad} onChange={handleChange} />
                <input type="text" name="codpos" placeholder="Código Postal" value={formData.codpos} onChange={handleChange} />
                <input type="text" name="municipio" placeholder="Municipio" value={formData.municipio} onChange={handleChange} />
                <input type="text" name="licencia_folio" placeholder="Folio Licencia" value={formData.licencia_folio} onChange={handleChange} required />
                <input type="text" name="licencia_tipo" placeholder="Tipo Licencia" value={formData.licencia_tipo} onChange={handleChange} required />
                <input type="date" name="licencia_vigencia" value={formData.licencia_vigencia} onChange={handleChange} required />
              </>
            ) : (
              <select name="chofer" value={formData.chofer || ""} onChange={handleChange} required>
                <option value="">Selecciona un chofer existente</option>
                {choferesExistentes.map(c => (
                  <option key={c.id_chofer} value={c.id_chofer}>{c.nombre} ({c.curp})</option>
                ))}
              </select>
            )}
          </>
        )}

        <div className="modal-actions">
          <button type="submit" className="btn-guardar">{usuarioToEdit ? "Actualizar" : "Registrar"}</button>
          <button type="button" className="btn-cancelar" onClick={onClose}>Cancelar</button>
        </div>
      </form>
    </Modal>
  );
};

export default RegistrarUsuario;
