import React, { useEffect, useState } from "react";
import Modal from "../components/Modal";
import Swal from "sweetalert2";
import { API_URL } from "../config";
import Select from "react-select";
import "./Unidades.css";

export default function Sucursales() {
  const [sucursales, setSucursales] = useState([]);
  const [empresas, setEmpresas] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    id_sucursal: null,
    nombre: "",
    direccion: "",
    telefono: "",
    correo: "",
    horario: "",
    id_empresa: null
  });

  // -----------------------------
  // Cargar sucursales y empresas
  // -----------------------------
  const fetchSucursales = async () => {
    const res = await fetch(`${API_URL}/sucursales`);
    const data = await res.json();
    setSucursales(data);
  };

  const fetchEmpresas = async () => {
    const res = await fetch(`${API_URL}/empresas`);
    const data = await res.json();
    setEmpresas(data);
  };

  useEffect(() => {
    fetchSucursales();
    fetchEmpresas();
  }, []);

  // -----------------------------
  // Manejo de inputs
  // -----------------------------
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleEmpresaChange = (option) => {
    setFormData({ ...formData, id_empresa: option ? option.value : null });
  };

  // -----------------------------
  // Crear / actualizar sucursal
  // -----------------------------
  const handleSubmit = async (e) => {
    e.preventDefault();
    const method = formData.id_sucursal ? "PUT" : "POST";
    const url = formData.id_sucursal
      ? `${API_URL}/sucursales/${formData.id_sucursal}`
      : `${API_URL}/sucursales`;

    try {
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (res.ok) {
        Swal.fire("Éxito", data.message, "success");
        setModalOpen(false);
        setFormData({
          id_sucursal: null,
          nombre: "",
          direccion: "",
          telefono: "",
          correo: "",
          horario: "",
          id_empresa: null
        });
        fetchSucursales();
      } else {
        Swal.fire("Error", data.error || "Algo salió mal", "error");
      }
    } catch (err) {
      Swal.fire("Error", "No se pudo procesar la solicitud", "error");
      console.error(err);
    }
  };

  // -----------------------------
  // Editar sucursal
  // -----------------------------
  const handleEdit = (sucursal) => {
    setFormData({ ...sucursal });
    setModalOpen(true);
  };

  // -----------------------------
  // Eliminar sucursal
  // -----------------------------
  const handleDelete = async (id) => {
    const result = await Swal.fire({
      title: "¿Deseas eliminar esta sucursal?",
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Sí, eliminar",
      cancelButtonText: "Cancelar"
    });
    if (!result.isConfirmed) return;

    try {
      const res = await fetch(`${API_URL}/sucursales/${id}`, { method: "DELETE" });
      const data = await res.json();
      Swal.fire("Éxito", data.message, "success");
      fetchSucursales();
    } catch (err) {
      Swal.fire("Error", "No se pudo eliminar la sucursal", "error");
    }
  };

  return (
    <div className="unidades-container">
      <h1>Sucursales</h1>

      <button
        className="btn-registrar-garantia"
        onClick={() => {
          setFormData({
            id_sucursal: null,
            nombre: "",
            direccion: "",
            telefono: "",
            correo: "",
            horario: "",
            id_empresa: null
          });
          setModalOpen(true);
        }}
      >
        Agregar Sucursal
      </button>

      {/* Tabla */}
      <div className="table-wrapper">
        <table className="elegant-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nombre</th>
              <th>Dirección</th>
              <th>Teléfono</th>
              <th>Correo</th>
              <th>Horario</th>
              <th>Empresa</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {sucursales.map((s) => {
              const empresa = empresas.find(e => e.id_empresa === s.id_empresa);
              return (
                <tr key={s.id_sucursal}>
                  <td>{s.id_sucursal}</td>
                  <td>{s.nombre}</td>
                  <td>{s.direccion}</td>
                  <td>{s.telefono}</td>
                  <td>{s.correo}</td>
                  <td>{s.horario}</td>
                  <td>{empresa ? empresa.nombre_comercial : "N/A"}</td>
                  <td>
                    <button onClick={() => handleEdit(s)}>✎</button>
                    <button onClick={() => handleDelete(s.id_sucursal)}>🗑</button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {modalOpen && (
        <Modal onClose={() => setModalOpen(false)}>
          <h2>{formData.id_sucursal ? "Editar Sucursal" : "Agregar Sucursal"}</h2>
          <form className="form-container" onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Nombre</label>
              <input
                type="text"
                name="nombre"
                value={formData.nombre}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Dirección</label>
              <input
                type="text"
                name="direccion"
                value={formData.direccion}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Teléfono</label>
              <input
                type="text"
                name="telefono"
                value={formData.telefono}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Correo</label>
              <input
                type="email"
                name="correo"
                value={formData.correo}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Horario</label>
              <input
                type="text"
                name="horario"
                value={formData.horario}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Empresa</label>
              <Select
                options={empresas.map(e => ({ value: e.id_empresa, label: e.nombre_comercial }))}
                value={
                  formData.id_empresa
                    ? { value: formData.id_empresa, label: empresas.find(e => e.id_empresa === formData.id_empresa)?.nombre_comercial }
                    : null
                }
                onChange={handleEmpresaChange}
                placeholder="Selecciona empresa"
              />
            </div>

            <button type="submit" className="btn-registrar-garantia">
              {formData.id_sucursal ? "Actualizar" : "Agregar"}
            </button>
          </form>
        </Modal>
      )}
    </div>
  );
}
