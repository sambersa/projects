using System.Globalization;
using System.Security;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace PipeTransfer;

public record TraceRow(int Scan, int ElapsedMs, Inputs Inputs, Snapshot Result);

// Fixed actuator delays, no inertia. A stopped clamp retains physical feedback.
internal sealed class Plant
{
    private Inputs sensors = new(AtBottom: true, ClampOpen: true);
    private int clampMs, liftMs, transferMs, lowerMs, releaseMs;
    public Inputs Sensors => sensors;
    public void Advance(Outputs output, int cycleMs, bool stalled)
    {
        if (stalled) return;
        if (output.Clamp && !sensors.ClampClosed)
        {
            clampMs += cycleMs;
            if (clampMs >= 300) sensors = sensors with { ClampClosed = true, ClampOpen = false };
        }
        if (output.Lift)
        {
            liftMs += cycleMs;
            sensors = sensors with { AtBottom = false, AtTop = liftMs >= 800 };
        }
        if (output.Transfer)
        {
            transferMs += cycleMs;
            sensors = sensors with { AtDestination = transferMs >= 1000 };
        }
        if (output.Lower)
        {
            lowerMs += cycleMs;
            sensors = sensors with { AtTop = false, AtBottom = lowerMs >= 800 };
        }
        if (output.Release)
        {
            releaseMs += cycleMs;
            if (releaseMs >= 300) sensors = sensors with { ClampClosed = false, ClampOpen = true };
        }
    }
}

public static class Simulation
{
    public static List<TraceRow> Run(string scenario)
    {
        if (scenario is not ("normal" or "guard-open" or "clamp-loss" or "actuator-stall"))
            throw new ArgumentException($"Unknown scenario: {scenario}");
        var controller = new Controller();
        var plant = new Plant();
        var trace = new List<TraceRow>();
        for (int scan = 0; scan < 120; scan++)
        {
            var inputs = plant.Sensors with { Start = scan == 1 };
            if (controller.Stage == Stage.Transferring && scenario == "guard-open")
                inputs = inputs with { GuardClosed = false };
            if (controller.Stage == Stage.Lifting && scenario == "clamp-loss")
                inputs = inputs with { ClampClosed = false };
            var result = controller.Scan(inputs);
            trace.Add(new(scan, scan * 100, inputs, result));
            if (result.Stage is Stage.Fault or Stage.Complete) return trace;
            plant.Advance(result.Outputs, 100, scenario == "actuator-stall");
        }
        throw new InvalidOperationException("Simulation exceeded its scan budget");
    }

    public static void WriteReports(string path, string scenario, List<TraceRow> trace)
    {
        Directory.CreateDirectory(path);
        var options = new JsonSerializerOptions { WriteIndented = true, Converters = { new JsonStringEnumConverter() } };
        File.WriteAllText(Path.Combine(path, "trace.json"), JsonSerializer.Serialize(trace, options) + "\n");
        var csv = new StringBuilder("scan,elapsed_ms,stage,clamp,lift,transfer,lower,release,fault\n");
        foreach (var row in trace)
        {
            var o = row.Result.Outputs;
            csv.AppendLine($"{row.Scan},{row.ElapsedMs},{row.Result.Stage},{o.Clamp},{o.Lift},{o.Transfer},{o.Lower},{o.Release},\"{row.Result.Fault}\"");
        }
        File.WriteAllText(Path.Combine(path, "trace.csv"), csv.ToString());
        File.WriteAllText(Path.Combine(path, "trace.svg"), Svg(scenario, trace));
    }

    private static string Svg(string scenario, List<TraceRow> trace)
    {
        var stages = new[] { Stage.Idle, Stage.Clamping, Stage.Lifting, Stage.Transferring, Stage.Lowering, Stage.Releasing, Stage.Complete, Stage.Fault };
        var svg = new StringBuilder("<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1100\" height=\"610\" viewBox=\"0 0 1100 610\" role=\"img\" aria-labelledby=\"title desc\">\n");
        svg.AppendLine($"<title id=\"title\">Pipe transfer simulation: {scenario}</title><desc id=\"desc\">State occupancy over simulated time. Each rectangle represents one 100 millisecond scan.</desc>");
        svg.AppendLine("<rect width=\"1100\" height=\"610\" fill=\"#0c202b\"/><g fill=\"#eaf4f5\" font-family=\"Segoe UI,Arial,sans-serif\">");
        svg.AppendLine("<text x=\"45\" y=\"46\" fill=\"#71cfc2\" font-size=\"13\" letter-spacing=\"3\">PIPE TRANSFER / SIMULATION TRACE</text>");
        svg.AppendLine($"<text x=\"45\" y=\"92\" font-size=\"32\" font-weight=\"700\">{scenario}</text>");
        svg.AppendLine($"<text x=\"45\" y=\"124\" font-size=\"15\" fill=\"#aac7cc\">{trace.Count} scans · {trace[^1].ElapsedMs / 1000.0:F1}s simulated · result: {trace[^1].Result.Stage}</text>");
        var step = 850.0 / trace.Count;
        for (int n = 0; n < stages.Length; n++)
        {
            int y = 165 + n * 43;
            svg.AppendLine($"<text x=\"45\" y=\"{y+22}\" font-size=\"14\">{stages[n]}</text><line x1=\"190\" x2=\"1040\" y1=\"{y+30}\" y2=\"{y+30}\" stroke=\"#284451\"/>");
            foreach(var row in trace.Where(r => r.Result.Stage == stages[n]))
            {
                string x = (190 + row.Scan * step).ToString("F2", CultureInfo.InvariantCulture);
                string width = (step + 0.1).ToString("F2", CultureInfo.InvariantCulture);
                string color = stages[n] == Stage.Fault ? "#f49b76" : "#71cfc2";
                svg.AppendLine($"<rect x=\"{x}\" y=\"{y}\" width=\"{width}\" height=\"30\" fill=\"{color}\"/>");
            }
        }
        var fault = SecurityElement.Escape(trace[^1].Result.Fault ?? "Sequence completed; no faults.");
        svg.AppendLine($"<text x=\"45\" y=\"555\" font-size=\"16\">{fault}</text>");
        svg.AppendLine("<text x=\"45\" y=\"585\" fill=\"#aac7cc\" font-size=\"12\">Synthetic equipment model · deterministic 100ms scans · no hardware connection</text></g></svg>");
        return svg.ToString();
    }
}
