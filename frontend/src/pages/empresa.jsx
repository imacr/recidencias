// Empresas.jsx
import React, { useEffect, useState } from "react";
import Swal from "sweetalert2";
import Modal from "../components/Modal"; // Modal reutilizable
import { API_URL } from "../config"; // URL global
import "./Unidades.css"; // Tus estilos

export default function Empresas() {
  const [empresas, setEmpresas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    id_empresa: null,
    razon_social: "",
    rfc: "",
    regimen_fiscal: "",
    nombre_comercial: "",
    direccion: "",
    inicio_operaciones: "",
    estatus: "",
    actividad_economica: ""
  });

  const fetchEmpresas = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/empresas`);
      const data = await res.json();
      setEmpresas(data);
    } catch (err) {
      console.error(err);
      Swal.fire("Error", "No se pudieron cargar las empresas", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmpresas();
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const method = formData.id_empresa ? "PUT" : "POST";
    const url = formData.id_empresa
      ? `${API_URL}/empresas/${formData.id_empresa}`
      : `${API_URL}/empresas`;

    try {
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!res.ok) throw new Error("Error en la operación");

      setModalOpen(false);
      setFormData({
        id_empresa: null,
        razon_social: "",
        rfc: "",
        regimen_fiscal: "",
        nombre_comercial: "",
        direccion: "",
        inicio_operaciones: "",
        estatus: "",
        actividad_economica: ""
      });

      fetchEmpresas();

      Swal.fire(
        formData.id_empresa ? "Actualizado" : "Agregado",
        formData.id_empresa
          ? "La empresa se actualizó correctamente"
          : "La empresa se agregó correctamente",
        "success"
      );
    } catch (err) {
      console.error(err);
      Swal.fire("Error", "No se pudo completar la operación", "error");
    }
  };

  const handleEdit = (empresa) => {
    setFormData({ ...empresa });
    setModalOpen(true);
  };

  const handleDelete = async (id) => {
    const result = await Swal.fire({
      title: "¿Deseas eliminar esta empresa?",
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Sí, eliminar",
      cancelButtonText: "Cancelar"
    });

    if (!result.isConfirmed) return;

    try {
      const res = await fetch(`${API_URL}/empresas/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Error al eliminar");

      fetchEmpresas();
      Swal.fire("Eliminado", "La empresa se eliminó correctamente", "success");
    } catch (err) {
      console.error(err);
      Swal.fire("Error", "No se pudo eliminar la empresa", "error");
    }
  };

  return (
    <div className="unidades-container">
      <h1>Empresas</h1>

      <button
        className="btn-registrar-garantia"
        onClick={() => {
          setFormData({
            id_empresa: null,
            razon_social: "",
            rfc: "",
            regimen_fiscal: "",
            nombre_comercial: "",
            direccion: "",
            inicio_operaciones: "",
            estatus: "",
            actividad_economica: ""
          });
          setModalOpen(true);
        }}
      >
        Agregar Empresa
      </button>

      <div className="table-wrapper">
        {loading ? (
          <p className="mensaje-estado">Cargando empresas...</p>
        ) : empresas.length === 0 ? (
          <p className="mensaje-estado error">No hay empresas para mostrar.</p>
        ) : (
          <table className="elegant-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Nombre Comercial</th>
                <th>Razón Social</th>
                <th>RFC</th>
                <th>Regimen Fiscal</th>
                <th>Dirección</th>
                <th>Inicio Operaciones</th>
                <th>Estatus</th>
                <th>Actividad Económica</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {empresas.map((e) => (
                <tr key={e.id_empresa}>
                  <td>{e.id_empresa}</td>
                  <td>{e.nombre_comercial}</td>
                  <td>{e.razon_social}</td>
                  <td>{e.rfc}</td>
                  <td>{e.regimen_fiscal}</td>
                  <td>{e.direccion}</td>
                  <td>{e.inicio_operaciones}</td>
                  <td>{e.estatus}</td>
                  <td>{e.actividad_economica}</td>
                  <td>
                    <div className="actions-container">
                      <button
                        className="icon-edit"
                        onClick={() => handleEdit(e)}
                      >
                        ✎
                      </button>
                      <button
                        className="icon-delete"
                        onClick={() => handleDelete(e.id_empresa)}
                      >
                        🗑
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {modalOpen && (
        <Modal onClose={() => setModalOpen(false)}>
          <h2>{formData.id_empresa ? "Editar Empresa" : "Agregar Empresa"}</h2>
          <form className="form-container" onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label>Nombre Comercial</label>
                <input
                  type="text"
                  name="nombre_comercial"
                  value={formData.nombre_comercial}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label>Razón Social</label>
                <input
                  type="text"
                  name="razon_social"
                  value={formData.razon_social}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>RFC</label>
                <input
                  type="text"
                  name="rfc"
                  value={formData.rfc}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label>Regimen Fiscal</label>
                <input
                  type="text"
                  name="regimen_fiscal"
                  value={formData.regimen_fiscal}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Dirección</label>
                <input
                  type="text"
                  name="direccion"
                  value={formData.direccion}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label>Inicio Operaciones</label>
                <input
                  type="date"
                  name="inicio_operaciones"
                  value={formData.inicio_operaciones}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

           <div className="form-row">
            <div className="form-group">
                <label>Estatus</label>
                <select
                name="estatus"
                value={formData.estatus}
                onChange={handleChange}
                required
                >
                <option value="">Selecciona</option>
                <option value="Activo">Activo</option>
                <option value="Inactivo">Inactivo</option>
                </select>
            </div>
            <div className="form-group">
                <label>Actividad Económica</label>
                <input
                type="text"
                name="actividad_economica"
                value={formData.actividad_economica}
                onChange={handleChange}
                required
                />
            </div>
            </div>


            <button type="submit" className="btn-registrar-garantia">
              {formData.id_empresa ? "Actualizar" : "Agregar"}
            </button>
          </form>
        </Modal>
      )}
    </div>
  );
}
