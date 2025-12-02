import React, { useState } from "react";
import Swal from "sweetalert2";
import { BASE_URL } from "../config";
import "./CambiarContraseña.css";
import { useNavigate } from "react-router-dom";

const CambiarContraseña = ({ usuarioId }) => {
  const [contraseña, setContraseña] = useState("");
  const [confirmarContraseña, setConfirmarContraseña] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!contraseña || !confirmarContraseña) {
      Swal.fire({
        title: "Error",
        text: "Debes llenar ambos campos",
        icon: "warning",
        confirmButtonColor: "#ffc107",
      });
      return;
    }

    if (contraseña !== confirmarContraseña) {
      Swal.fire({
        title: "Error",
        text: "Las contraseñas no coinciden",
        icon: "error",
        confirmButtonColor: "#dc3545",
      });
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${BASE_URL}/api/usuarios/${usuarioId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ contraseña }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText);
      }

      Swal.fire({
        title: "¡Éxito!",
        text: "Contraseña actualizada correctamente",
        icon: "success",
        confirmButtonColor: "#28a745",
      });

      setContraseña("");
      setConfirmarContraseña("");
      navigate("/"); // regreso al dashboard
    } catch (err) {
      console.error(err);
      Swal.fire({
        title: "Error",
        text: `No se pudo actualizar la contraseña: ${err.message}`,
        icon: "error",
        confirmButtonColor: "#dc3545",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="cambiar-password-page">
      <div className="form-container">
        <h2 className="form-title">Cambiar Contraseña</h2>
        <form onSubmit={handleSubmit} className="form-content">
          <input
            type="password"
            placeholder="Nueva contraseña"
            value={contraseña}
            onChange={(e) => setContraseña(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Confirmar contraseña"
            value={confirmarContraseña}
            onChange={(e) => setConfirmarContraseña(e.target.value)}
            required
          />
          <div className="form-actions">
            <button type="submit" className="btn-guardar" disabled={loading}>
              {loading ? "Actualizando..." : "Actualizar"}
            </button>
            <button
              type="button"
              className="btn-cancelar"
              onClick={() => navigate(-1)}
            >
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CambiarContraseña;
