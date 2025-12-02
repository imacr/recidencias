import React, { useEffect, useState } from 'react';
import './Unidades.CSS'; 
import RegistrarUsuario from "./RegistrarUsuario";
import { API_URL } from "../config"; 

const Usuarios = () => {
  const [usuarios, setUsuarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [usuarioToEdit, setUsuarioToEdit] = useState(null); // Usuario seleccionado para editar
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPageOptions = [5, 10, 20];
  const [itemsPerPage, setItemsPerPage] = useState(5);

  const indexOfLast = currentPage * itemsPerPage;
  const indexOfFirst = indexOfLast - itemsPerPage;
  const currentUsuarios = usuarios.slice(indexOfFirst, indexOfLast);
  const totalPages = Math.ceil(usuarios.length / itemsPerPage);

  const agregarUsuario = (newUser) => {
    const exists = usuarios.find(u => u.id_usuario === newUser.id_usuario);
    if (exists) {
      // Actualiza el usuario editado
      setUsuarios(usuarios.map(u => u.id_usuario === newUser.id_usuario ? newUser : u));
    } else {
      // Agrega nuevo usuario
      setUsuarios([...usuarios, newUser]);
    }
  };

  useEffect(() => {
    const fetchUsuarios = async () => {
      try {
        const response = await fetch(`${API_URL}/api/usuarios`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Error: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        setUsuarios(data);
      } catch (err) {
        setError(err.message);
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchUsuarios();
  }, []);

  const handleDeleteUsuario = async (id_usuario) => {
    if (!window.confirm("¿Estás seguro de eliminar este usuario?")) return;

    try {
      const response = await fetch(`${API_URL}/api/usuarios/${id_usuario}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error("No se pudo eliminar el usuario");

      setUsuarios(usuarios.filter(u => u.id_usuario !== id_usuario));
    } catch (err) {
      console.error(err);
      alert("Error al eliminar usuario: " + err.message);
    }
  };

  if (loading) return <div className="mensaje-estado">Cargando usuarios...</div>;
  if (error) return <div className="mensaje-estado error">{error}</div>;

  return (
    <div className="unidades-container">
      <h1><i className="fa-solid fa-users-gear"></i> Usuarios</h1>

      <div className="pagination-controls">
        <label>
          Mostrar:
          <select
            value={itemsPerPage}
            onChange={e => {
              setItemsPerPage(Number(e.target.value));
              setCurrentPage(1);
            }}
          >
            {itemsPerPageOptions.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        </label>

        <button className="btn-registrar-garantia" onClick={() => { setUsuarioToEdit(null); setShowModal(true); }}>
          Registrar Usuario
        </button>

        <RegistrarUsuario
          show={showModal}
          onClose={() => setShowModal(false)}
          onCreate={agregarUsuario}
          usuarioToEdit={usuarioToEdit}
        />
      </div>

      <div className="table-wrapper">
        <table className="elegant-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nombre</th>
              <th>Usuario</th>
              <th>Correo</th>
              <th>Rol</th>
              <th>Estado</th>
              <th>Fecha Registro</th>
              <th>Último Login</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {currentUsuarios.map(u => (
              <tr key={u.id_usuario}>
                <td>{u.id_usuario}</td>
                <td>{u.nombre}</td>
                <td>{u.usuario}</td>
                <td>{u.correo}</td>
                <td>{u.rol}</td>
                <td>{u.estado}</td>
                <td>{new Date(u.fecha_registro).toLocaleString()}</td>
                <td>{u.fecha_ultimo_login ? new Date(u.fecha_ultimo_login).toLocaleString() : 'N/A'}</td>
                <td>
                  <div className="actions-container">
                    <button onClick={() => { setUsuarioToEdit(u); setShowModal(true); }}>
                      <i className="fa-solid fa-pen-to-square icon-edit"></i>
                    </button>

                    <button onClick={() => handleDeleteUsuario(u.id_usuario)}>
                      <i className="fa-solid fa-trash icon-delete"></i>
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card-wrapper">
        {currentUsuarios.map(u => (
          <div key={u.id_usuario} className="unidad-card">
            <h3>{u.nombre} ({u.usuario})</h3>
            <p><b>ID:</b> {u.id_usuario}</p>
            <p><b>Correo:</b> {u.correo}</p>
            <p><b>Rol:</b> {u.rol}</p>
            <p><b>Estado:</b> {u.estado}</p>
            <p><b>Fecha Registro:</b> {new Date(u.fecha_registro).toLocaleDateString()}</p>
            <p><b>Último Login:</b> {u.fecha_ultimo_login ? new Date(u.fecha_ultimo_login).toLocaleDateString() : 'N/A'}</p>
            <div className="actions-container">
              <button onClick={() => { setUsuarioToEdit(u); setShowModal(true); }}>
                <i className="fa-solid fa-pen-to-square icon-edit"></i>
              </button>

              <button onClick={() => handleDeleteUsuario(u.id_usuario)}>
                <i className="fa-solid fa-trash icon-delete"></i>
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="pagination">
        <button onClick={() => setCurrentPage(p => Math.max(p - 1, 1))} disabled={currentPage === 1}><i className="fa-solid fa-arrow-left"></i></button>
        <span>Página {currentPage} de {totalPages}</span>
        <button onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))} disabled={currentPage === totalPages}>
          <i className="fa-solid fa-arrow-right"></i>
        </button>
      </div>
    </div>
  );
};

export default Usuarios;
