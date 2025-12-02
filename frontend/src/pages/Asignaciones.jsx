import { useEffect, useState } from "react";
import Swal from "sweetalert2";
import { API_URL } from "../config";
import "./Unidades.css";

export default function AsignacionesActivas() {
  const [asignaciones, setAsignaciones] = useState([]);
  const [choferes, setChoferes] = useState([]);
  const [unidades, setUnidades] = useState([]);
  const [loading, setLoading] = useState(true);

  const [choferSeleccionado, setChoferSeleccionado] = useState("");
  const [unidadSeleccionada, setUnidadSeleccionada] = useState("");
const [unidadesLibres, setUnidadesLibres] = useState([]); // solo libres



const fetchDatos = async () => {
  try {
    const [resAsign, resChofer, resUnidades, resLibres] = await Promise.all([
      fetch(`${API_URL}/asignaciones`),
      fetch(`${API_URL}/choferes`),
      fetch(`${API_URL}/unidades`),          // todas
      fetch(`${API_URL}/unidades/libres`)    // solo libres
    ]);

    const [asignData, choferData, unidadesData, libresData] = await Promise.all([
      resAsign.json(),
      resChofer.json(),
      resUnidades.json(),
      resLibres.json()
    ]);

    setAsignaciones(asignData);
    setChoferes(choferData);
    setUnidades(unidadesData);       // tabla
    setUnidadesLibres(libresData);   // select
  } catch (err) {
    console.error(err);
    Swal.fire("Error", "No se pudieron cargar los datos", "error");
  } finally {
    setLoading(false);
  }
};


  useEffect(() => { fetchDatos(); }, []);

  const asignarChofer = async () => {
    if (!choferSeleccionado || !unidadSeleccionada) {
      Swal.fire("Atención", "Selecciona chofer y unidad", "warning");
      return;
    }



    try {
      const res = await fetch(`${API_URL}/asignaciones`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id_chofer: choferSeleccionado,
          id_unidad: unidadSeleccionada,
          usuario: "admin"
        })
      });
      const data = await res.json();
      if (res.ok) Swal.fire("Éxito", data.message, "success");
      else Swal.fire("Error", data.error, "error");

      setChoferSeleccionado("");
      setUnidadSeleccionada("");
      fetchDatos();
    } catch (err) {
      console.error(err);
      Swal.fire("Error", "No se pudo asignar", "error");
    }
  };

  const finalizarAsignacion = async (id_asignacion) => {
    try {
      const res = await fetch(`${API_URL}/asignaciones/${id_asignacion}/finalizar`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ usuario: "admin" })
      });
      const data = await res.json();
      if (res.ok) Swal.fire("Éxito", data.message, "success");
      else Swal.fire("Error", data.error, "error");
      fetchDatos();
    } catch (err) {
      console.error(err);
      Swal.fire("Error", "No se pudo finalizar asignación", "error");
    }
  };

  if (loading) return <p>Cargando datos...</p>;

  // Filtramos choferes que no tengan asignación activa
  const choferesDisponibles = choferes.filter(
    c => !asignaciones.some(a => a.id_chofer === c.id_chofer && !a.fecha_fin)
  );

  // Funciones para mostrar nombre completo
  const nombreChofer = id => choferes.find(c => c.id_chofer === id)?.nombre || id;
const nombreUnidad = (id) => {
  const u = unidades.find((u) => u.id_unidad === id);
  return u
    ? `${u.id_unidad} - ${u.vehiculo} (${u.placa || "Sin placa"})`
    : id;
};


  return (
    <div className="unidades-container">
      <h2>Asignaciones Activas</h2>

      <h4 style={{ marginTop: "30px" }}>Asignar Chofer a Unidad</h4>
      <div className="asignar-form" style={{
        display: "flex",
        gap: "10px",
        flexWrap: "wrap",
        alignItems: "center",
        marginTop: "10px",
        padding: "15px",
        border: "1px solid #ccc",
        borderRadius: "8px",
        backgroundColor: "#f9f9f9"
      }}>
       <select
        value={choferSeleccionado}
        onChange={e => setChoferSeleccionado(e.target.value)}
        style={{ padding: "8px", borderRadius: "5px", minWidth: "200px" }}
      >
        <option value="">--Selecciona Chofer--</option>
        {choferes.map(c => (
          <option key={c.id_chofer} value={c.id_chofer}>{c.nombre}</option>
        ))}
      </select>


        <select
        value={unidadSeleccionada}
        onChange={(e) => setUnidadSeleccionada(e.target.value)}
        style={{ padding: "8px", borderRadius: "5px", minWidth: "200px" }}
      >
        <option value="">--Selecciona Unidad--</option>
        {unidadesLibres.map((u) => (
          <option key={u.id_unidad} value={u.id_unidad}>
            {u.id_unidad} - {u.nombre}
          </option>
        ))}
      </select>


        <button
          onClick={asignarChofer}
          style={{
            padding: "8px 15px",
            backgroundColor: "#4caf50",
            color: "white",
            border: "none",
            borderRadius: "5px",
            cursor: "pointer"
          }}
        >
          Asignar
        </button>
      </div>

      <table className="elegant-table" style={{ marginTop: "20px" }}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Chofer</th>
            <th>Unidad</th>
            <th>Fecha Asignación</th>
            <th>Fecha Fin</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {asignaciones.length > 0 ? asignaciones.map(a => (
            <tr key={a.id_asignacion}>
              <td>{a.id_asignacion}</td>
              <td>{nombreChofer(a.id_chofer)}</td>
              <td>{nombreUnidad(a.id_unidad)}</td>
              <td>{a.fecha_asignacion}</td>
              <td>{a.fecha_fin || "-"}</td>
              <td>
                {!a.fecha_fin ? (
                  <button className="btn-finalizar" onClick={() => finalizarAsignacion(a.id_asignacion)}>Desasignar</button>
                ) : (
                  <span>Finalizada</span>
                )}
              </td>
            </tr>
          )) : (
            <tr>
              <td colSpan="6" style={{ textAlign: "center" }}>No hay asignaciones</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
