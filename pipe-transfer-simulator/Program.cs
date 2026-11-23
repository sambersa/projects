using PipeTransfer;
using System.Text.Json;
using System.Text.Json.Serialization;

if (args.SequenceEqual(new[] { "--test" })) return ControllerTests.Run();
string scenario = "normal";
string? output = null;
for (int n = 0; n < args.Length; n++)
{
    if (args[n] == "--fault") scenario = "guard-open";
    else if (args[n] == "--scenario" && n + 1 < args.Length) scenario = args[++n];
    else if (args[n] == "--out" && n + 1 < args.Length) output = args[++n];
    else
    {
        Console.Error.WriteLine("Usage: dotnet run -- [--test | --scenario normal|guard-open|clamp-loss|actuator-stall [--out directory]]");
        return 2;
    }
}
try
{
    var trace = Simulation.Run(scenario);
    var options = new JsonSerializerOptions { Converters = { new JsonStringEnumConverter() } };
    foreach (var row in trace) Console.WriteLine(JsonSerializer.Serialize(row, options));
    if (output is not null) Simulation.WriteReports(output, scenario, trace);
    return 0;
}
catch (Exception e) when (e is ArgumentException or IOException or UnauthorizedAccessException)
{
    Console.Error.WriteLine(e.Message);
    return 2;
}
