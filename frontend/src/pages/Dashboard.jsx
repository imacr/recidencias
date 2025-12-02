// src/components/DashboardUnidades.jsx
import React, { useEffect, useState } from "react";
import { BASE_URL } from "../config";
import { Bar, Pie } from "react-chartjs-2";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from "chart.js";
import "./Dashboard.css";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

export default function DashboardUnidades() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [verGraficoSinPoliza, setVerGraficoSinPoliza] = useState(false);

  useEffect(() => {
    fetch(`${BASE_URL}/api/dashboard/unidades_completo`)
      .then((res) => res.json())
      .then((data) => {
        setDashboard(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error al obtener dashboard:", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="text-center mt-5">Cargando...</div>;
  if (!dashboard) return <div className="text-center mt-5">No hay datos</div>;

  const { totales, por_sucursal, por_aseguradora, unidades_sin_poliza } = dashboard;

  const estadoColor = (estado) => {
    switch (estado) {
      case "ATRASADA":
        return "estado-atrasada";
      case "EN TIEMPO":
        return "estado-en-tiempo";
      case "PENDIENTE":
        return "estado-pendiente";
      default:
        return "estado-otro";
    }
  };

  const sucursalesFiltradas = por_sucursal.filter((s) => s && s.sucursal && (
    s.unidades > 0 || s.polizas > 0 || s.verificacion_activa > 0 ||
    s.verificacion_vencida > 0 || s.sin_verificacion > 0 ||
    (s.proxima_verificacion && s.proxima_verificacion !== "N/A")
  ));

  // Datos gráficas
  const dataSucursales = {
    labels: sucursalesFiltradas.map((s) => s.sucursal),
    datasets: [{
      label: "Unidades por Sucursal",
      data: sucursalesFiltradas.map((s) => s.unidades),
      backgroundColor: "rgba(255, 99, 132, 0.7)",
      borderRadius: 6,
    }]
  };

  const dataAseguradoras = {
    labels: por_aseguradora.map((a) => a.aseguradora),
    datasets: [{
      label: "Pólizas por Aseguradora",
      data: por_aseguradora.map((a) => a.total_polizas),
      backgroundColor: ["#ff2e2e", "#333", "#ff5555", "#660000"],
      borderRadius: 6,
    }]
  };

  return (
    <div className="dashboard-container">
      <h2 className="dashboard-title">Dashboard de unidades</h2>

      {/* Totales */}
      <div className="totales-row">
        <div className="total-card total-unidades">
          <h6>Total unidades</h6>
          <p>{totales.total_unidades}</p>
        </div>
        <div className="total-card total-polizas">
          <h6>Total pólizas</h6>
          <p>{totales.total_polizas}</p>
        </div>
        <div className="total-card total-ver-activa">
          <h6>Verificación activa</h6>
          <p>{totales.verificacion_activa}</p>
        </div>
        <div className="total-card total-ver-vencida">
          <h6>Verificación vencida</h6>
          <p>{totales.verificacion_vencida}</p>
        </div>
        <div className="total-card total-sin-ver">
          <h6>Sin verificación</h6>
          <p>{totales.sin_verificacion}</p>
        </div>
      </div>

      {/* Gráficas */}
      <div className="graficas-row">
        <div className="grafica-card">
          <h5>Unidades por sucursal</h5>
          <div className="grafica-wrapper">
            <Bar data={dataSucursales} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
        </div>
        <div className="grafica-card">
          <h5>Pólizas por aseguradora</h5>
          <div className="grafica-wrapper">
            <Pie data={dataAseguradoras} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
        </div>
      </div>

      {/* Por Sucursal */}
      <h4 className="section-title">Por sucursal</h4>
      <div className="sucursales-row">
        {sucursalesFiltradas.map((s) => (
          <div className="sucursal-card" key={s.sucursal}>
            <h6>{s.sucursal}</h6>
            <p>Unidades: {s.unidades}</p>
            <p>Pólizas: {s.polizas}</p>
            <p>Verificación activa: {s.verificacion_activa}</p>
            <p>Verificación vencida: {s.verificacion_vencida}</p>
            <p>Sin verificación: {s.sin_verificacion}</p>
            <p>Próxima verificación: {s.proxima_verificacion || "N/A"}</p>
            <p className={estadoColor(s.estado_verificacion)}>Estado: {s.estado_verificacion}</p>
          </div>
        ))}
      </div>

      {/* Unidades con/sin póliza */}
      <div className="sin-poliza-section">
        <div className="section-header">
          <h4 className="section-title">Unidades con y sin póliza</h4>
          <button className="btn-toggle" onClick={() => setVerGraficoSinPoliza(!verGraficoSinPoliza)}>
            {verGraficoSinPoliza ? "Ver Tabla" : "Ver Gráfica"}
          </button>
        </div>

        {verGraficoSinPoliza ? (
          <div className="grafica-card">
            <div className="grafica-wrapper">
              <Pie
                data={{
                  labels: ["Con Póliza", "Sin Póliza"],
                  datasets: [{
                    label: "Unidades",
                    data: [
                      totales.total_unidades - unidades_sin_poliza.length,
                      unidades_sin_poliza.length,
                    ],
                    backgroundColor: ["#28a745", "#dc3545"],
                    borderColor: ["#1c7c31", "#a71d2a"],
                    borderWidth: 2,
                  }]
                }}
                options={{ responsive: true, maintainAspectRatio: false }}
              />
            </div>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>ID unidad</th>
                  <th>Marca</th>
                  <th>Vehículo</th>
                  <th>Sucursal</th>
                </tr>
              </thead>
              <tbody>
                {unidades_sin_poliza.length > 0 ? unidades_sin_poliza.map((u) => (
                  <tr key={u.id_unidad}>
                    <td>{u.id_unidad}</td>
                    <td>{u.marca}</td>
                    <td>{u.vehiculo}</td>
                    <td>{u.sucursal}</td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={4} className="text-center">Todas las unidades tienen póliza</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
