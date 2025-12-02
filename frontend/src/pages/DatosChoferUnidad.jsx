import React, { useState, useEffect } from "react";
import { API_URL } from "../config";
import "./DatosChoferUnidad.css";

export default function DatosChoferUnidad() {
  const [datos, setDatos] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDatos = async () => {
      const idUsuario = localStorage.getItem("usuarioId");
      try {
        const res = await fetch(`${API_URL}/chofer/unidad/${idUsuario}`);
        if (!res.ok) throw new Error("No se pudieron cargar los datos");
        const data = await res.json();


        setDatos(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchDatos();
  }, []);

  if (loading) return <p className="cargando">Cargando datos...</p>;
  if (error) return <p className="error">Error: {error}</p>;
  if (!datos) return <p className="no-datos">No hay datos disponibles</p>;

  const { chofer, unidad, usuario } = datos;

  const handleEditarChofer = () => {
    alert(`Editar chofer: ${chofer.nombre}`);
  };

  return (
    <div className="datos-container">
      <h1 className="titulo">Datos del Chofer y Unidad</h1>


      {/* DATOS DEL CHOFER */}
      <section className="tarjeta chofer">
        <h2>Chofer</h2>

        <p><strong>Nombre completo:</strong> {chofer.nombre}</p>
        <p><strong>Usuario:</strong> {usuario.usuario}</p>
        <p><strong>Correo:</strong> {usuario.correo}</p>
        <p><strong>Rol:</strong> {usuario.rol}</p>
        <p><strong>Estado:</strong> {usuario.estado}</p>
        <p><strong>Fecha de registro:</strong> {usuario.fecha_registro}</p>
        <p><strong>Último login:</strong> {usuario.fecha_ultimo_login || "Nunca"}</p>
        <p><strong>CURP:</strong> {chofer.curp}</p>
        <p><strong>Licencia:</strong> {chofer.licencia_tipo} ({chofer.licencia_vigencia || "No especificada"})</p>
        <p><strong>Calle:</strong> {chofer.calle || "No especificada"}</p>
        <p><strong>Colonia / Localidad:</strong> {chofer.colonia_localidad || "No especificada"}</p>
        <p><strong>Código Postal:</strong> {chofer.codpos || "No especificado"}</p>
        <p><strong>Municipio:</strong> {chofer.municipio || "No especificado"}</p>

        <button className="btn-editar" onClick={handleEditarChofer}>Editar chofer</button>
      </section>

      {/* DATOS DE LA UNIDAD */}
        {unidad && (
        <section className="unidad tarjeta">
            <h2>Unidad Asignada</h2>

            {unidad.url_foto && (
            <div className="imagen-unidad">
                <img
                src={
                    unidad.url_foto.startsWith("http")
                    ? unidad.url_foto
                    : `${API_URL}/${unidad.url_foto}`   // FIX
                }
                alt="Unidad"
                />
            </div>
            )}

            <p><strong>ID Unidad:</strong> {unidad.id_unidad}</p>
            <p><strong>Marca:</strong> {unidad.marca}</p>
            <p><strong>Modelo:</strong> {unidad.modelo}</p>

            {/* Placa real */}
            <p><strong>Placas:</strong> 
            {unidad.placa && unidad.placa.placa ? unidad.placa.placa : "Sin placa registrada"}
            </p>

            <p><strong>Color:</strong> {unidad.color}</p>
        </section>
        )}

    </div>
  );
}
