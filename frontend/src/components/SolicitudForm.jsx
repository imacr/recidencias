import React, { useState, useEffect } from "react";
import Swal from "sweetalert2";
import "./SolicitudForm.css";
import { API_URL } from "../config";

export default function SolicitudFallaPaso1y2() {
  const [unidades, setUnidades] = useState([]);
  const [piezas, setPiezas] = useState([]);
  const [marcas, setMarcas] = useState([]);
  const [lugares, setLugares] = useState([]);
  const [misSolicitudes, setMisSolicitudes] = useState([]);
  const [fallaData, setFallaData] = useState({}); // por solicitud

  const idChofer = localStorage.getItem("usuarioId");
  const rol = localStorage.getItem("rol");

  const [formData, setFormData] = useState({
    id_unidad: "",
    id_pieza: "",
    id_marca: "",
    tipo_servicio: "",
    descripcion: "",
    id_chofer: idChofer || "",
  });

  // Carga de solicitudes del chofer
  const cargarSolicitudes = async () => {
    if (!idChofer) return;
    try {
      const res = await fetch(`${API_URL}/solicitudes/chofer/${idChofer}`);
      const data = await res.json();
      const filtradas = data.filter(
        s => s.estado === "pendiente" || (s.estado === "aprobada" && !s.completada)
      );
      setMisSolicitudes(filtradas);
    } catch (err) {
      Swal.fire("Error", "No se pudieron cargar las solicitudes", "error");
    }
  };

  // Carga inicial de datos
  useEffect(() => {
    if (!idChofer) return;

    const cargarDatos = async () => {
      try {
        const [piezasRes, marcasRes, lugaresRes] = await Promise.all([
          fetch(`${API_URL}/piezas`).then(r => r.json()),
          fetch(`${API_URL}/marcas`).then(r => r.json()),
          fetch(`${API_URL}/lugares`).then(r => r.json()),
        ]);

        setPiezas(piezasRes);
        setMarcas(marcasRes);
        setLugares(lugaresRes);

        if (rol === "chofer") {
          const resUnidad = await fetch(`${API_URL}/unidades/chofer/${idChofer}`);
          const unidadChofer = await resUnidad.json();

          if (resUnidad.ok && unidadChofer.id_unidad) {
            setUnidades([unidadChofer]);
            setFormData(prev => ({ ...prev, id_unidad: unidadChofer.id_unidad }));
          } else {
            setUnidades([]);
            Swal.fire("Sin asignación", "No tienes una unidad asignada actualmente", "info");
          }
        } else {
          const unidadesRes = await fetch(`${API_URL}/unidades`).then(r => r.json());
          setUnidades(unidadesRes);
        }

        await cargarSolicitudes();
      } catch (err) {
        Swal.fire("Error", "Error al cargar los datos", "error");
      }
    };

    cargarDatos();
  }, [idChofer, rol]);

  // Manejo de inputs principales
  const handleChange = e => setFormData({ ...formData, [e.target.name]: e.target.value });

  // Manejo de inputs de fallas por solicitud
  const handleChangeFalla = (e, id_solicitud) => {
    const { name, value, type, checked, files } = e.target;
    setFallaData(prev => ({
      ...prev,
      [id_solicitud]: {
        ...prev[id_solicitud],
        [name]: type === "checkbox" ? checked : type === "file" ? files[0] : value,
      },
    }));
  };

  // Enviar nueva solicitud
  const handleSubmitSolicitud = async e => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_URL}/solicitudes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      const data = await res.json();

      if (res.ok) {
        Swal.fire("Enviado", "Solicitud enviada correctamente", "success");
        setFormData({
          id_unidad: rol === "chofer" ? unidades[0]?.id_unidad || "" : "",
          id_pieza: "",
          id_marca: "",
          tipo_servicio: "",
          descripcion: "",
          id_chofer: idChofer || "",
        });
        await cargarSolicitudes();
      } else {
        Swal.fire("Error", data.error || "No se pudo enviar la solicitud", "error");
      }
    } catch (err) {
      Swal.fire("Error", "No se pudo enviar la solicitud", "error");
    }
  };

  // Registrar falla
  const handleSubmitFalla = async id_solicitud => {
    const data = fallaData[id_solicitud];
    if (!data) return;

    const fd = new FormData();
    fd.append("id_solicitud", id_solicitud);
    fd.append("id_lugar", data.id_lugar || "");
    fd.append("proveedor", data.proveedor || "");
    fd.append("tipo_pago", data.tipo_pago || "");
    fd.append("costo", data.costo || "");
    fd.append("tiempo_uso_pieza", data.tiempo_uso_pieza || "");
    fd.append("aplica_poliza", data.aplica_poliza ? "true" : "false");
    fd.append("observaciones", data.observaciones || "");
    if (data.url_comprobante) fd.append("comprobante", data.url_comprobante);

    try {
      const res = await fetch(`${API_URL}/fallas`, { method: "POST", body: fd });
      const json = await res.json();
      if (res.ok) {
        Swal.fire("Registrado", json.msg, "success");
        setFallaData(prev => ({ ...prev, [id_solicitud]: {} }));
        await cargarSolicitudes();
      } else {
        Swal.fire("Error", json.error || "No se pudo registrar la falla", "error");
      }
    } catch (err) {
      Swal.fire("Error", "Error al registrar la falla", "error");
    }
  };

  return (
    <div className="form-container">

      {/* FORMULARIO PRINCIPAL - siempre visible */}
      {rol === "chofer" && unidades.length === 0 ? (
        <div className="form-card">
          <h3>No tienes unidad asignada</h3>
        </div>
      ) : (
        <div className="form-card">
          <h2 className="form-title">Solicitud de Falla Mecánica</h2>
          <form onSubmit={handleSubmitSolicitud} className="form-grid-2cols">
            <div className="form-group">
              <label>Unidad:</label>
              {rol === "chofer" ? (
                <input type="text" value={unidades[0]?.vehiculo || ""} readOnly />
              ) : (
                <select name="id_unidad" value={formData.id_unidad} onChange={handleChange} required>
                  <option value="">Seleccione</option>
                  {unidades.map(u => <option key={u.id_unidad} value={u.id_unidad}>{u.vehiculo}</option>)}
                </select>
              )}
            </div>

            <div className="form-group">
              <label>Pieza:</label>
              <select name="id_pieza" value={formData.id_pieza} onChange={handleChange} required>
                <option value="">Seleccione</option>
                {piezas.map(p => <option key={p.id_pieza} value={p.id_pieza}>{p.nombre_pieza}</option>)}
              </select>
            </div>

            <div className="form-group">
              <label>Marca:</label>
              <select name="id_marca" value={formData.id_marca} onChange={handleChange} required>
                <option value="">Seleccione</option>
                {marcas.map(m => <option key={m.id_marca} value={m.id_marca}>{m.nombre_marca}</option>)}
              </select>
            </div>

            <div className="form-group">
              <label>Tipo de servicio:</label>
              <select
                name="tipo_servicio"
                value={formData.tipo_servicio}
                onChange={handleChange}
                required
              >
                <option value="">Selecciona una opción</option>
                <option value="CORRECTIVO">Correctivo</option>
                <option value="PREVENTIVO">Preventivo</option>
                <option value="TRÁMITE">Trámite</option>
              </select>
            </div>


            <div className="form-group">
              <label>Descripción:</label>
              <textarea name="descripcion" value={formData.descripcion} onChange={handleChange}></textarea>
            </div>

            <div className="form-group full-width-btn">
              <button type="submit" className="submit-btn">Enviar Solicitud</button>
            </div>
          </form>
        </div>
      )}

      {/* FORMULARIOS PARA REGISTRAR FALLAS DE SOLICITUDES APROBADAS */}
      {misSolicitudes.filter(s => s.estado === "aprobada" && !s.completada).map(s => (
        <div key={s.id_solicitud} className="form-card mb-4">
          <h3 className="form-title">Registrar Falla para solicitud #{s.id_solicitud}</h3>

          <div className="form-grid-2cols">
            <div className="form-group">
              <label>Unidad:</label>
              <input type="text" value={s.unidad} readOnly />
            </div>

            <div className="form-group">
              <label>Pieza:</label>
              <input type="text" value={s.pieza} readOnly />
            </div>

            <div className="form-group">
              <label>Marca:</label>
              <input type="text" value={s.marca} readOnly />
            </div>

            <div className="form-group">
              <label>Servicio:</label>
              <input type="text" value={s.tipo_servicio} readOnly />
            </div>

            <div className="form-group">
              <label>Descripción:</label>
              <textarea value={s.descripcion} readOnly />
            </div>
          </div>

          {/* Formulario de registrar falla */}
          <form onSubmit={e => { e.preventDefault(); handleSubmitFalla(s.id_solicitud); }} className="form-grid-2cols mt-4">
            <div className="form-group">
              <label>Lugar de reparación:</label>
              <select name="id_lugar" value={fallaData[s.id_solicitud]?.id_lugar || ""} onChange={e => handleChangeFalla(e, s.id_solicitud)} required>
                <option value="">Seleccione</option>
                {lugares.map(l => <option key={l.id_lugar} value={l.id_lugar}>{l.nombre_lugar}</option>)}
              </select>
            </div>

            <div className="form-group">
              <label>Proveedor:</label>
              <input type="text" name="proveedor" value={fallaData[s.id_solicitud]?.proveedor || ""} onChange={e => handleChangeFalla(e, s.id_solicitud)} />
            </div>

            <div className="form-group">
              <label>Tipo de pago:</label>
              <select
                name="tipo_pago"
                value={fallaData[s.id_solicitud]?.tipo_pago || ""}
                onChange={e => handleChangeFalla(e, s.id_solicitud)}
              >
                <option value="">Seleccione un tipo de pago</option>
                <option value="Efectivo">Efectivo</option>
                <option value="Crédito">Crédito</option>
                <option value="Transferencia">Transferencia</option>
              </select>
            </div>


            <div className="form-group">
              <label>Costo:</label>
              <input type="number" name="costo" value={fallaData[s.id_solicitud]?.costo || ""} onChange={e => handleChangeFalla(e, s.id_solicitud)} />
            </div>

            <div className="form-group">
              <label>Tiempo uso pieza:</label>
              <input type="text" name="tiempo_uso_pieza" value={fallaData[s.id_solicitud]?.tiempo_uso_pieza || ""} onChange={e => handleChangeFalla(e, s.id_solicitud)} />
            </div>

            <div className="form-group">
              <label>
                <input type="checkbox" name="aplica_poliza" checked={fallaData[s.id_solicitud]?.aplica_poliza || false} onChange={e => handleChangeFalla(e, s.id_solicitud)} />
                Aplica póliza
              </label>
            </div>

            <div className="form-group">
              <label>Observaciones:</label>
              <textarea name="observaciones" value={fallaData[s.id_solicitud]?.observaciones || ""} onChange={e => handleChangeFalla(e, s.id_solicitud)}></textarea>
            </div>

            <div className="form-group">
              <label>Comprobante (PDF):</label>
              <input type="file" name="url_comprobante" accept="application/pdf" onChange={e => handleChangeFalla(e, s.id_solicitud)} />
            </div>

            <div className="form-group full-width-btn">
              <button type="submit" className="submit-btn">Registrar Falla</button>
            </div>
          </form>
        </div>
      ))}
    </div>
  );
}
