namespace PipeTransfer;

internal static class ControllerTests
{
    private static void Check(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
    }
    private static void NoMotion(Snapshot s) => Check(s.Outputs == new Outputs(false, false, false, false, false), "Outputs energized");
    private static Controller Moving()
    {
        var c = new Controller(); c.Scan(new(Start: true)); c.Scan(new(ClampClosed: true)); return c;
    }
    public static int Run()
    {
        (string Name, Action Test)[] tests = [
            ("full sequence and held start", () => {
                var c = new Controller();
                Inputs[] scans = [new(Start:true), new(Start:true,ClampClosed:true),
                    new(Start:true,ClampClosed:true,AtTop:true), new(Start:true,ClampClosed:true,AtDestination:true),
                    new(Start:true,ClampClosed:true,AtBottom:true), new(Start:true,ClampOpen:true)];
                Stage[] expected = [Stage.Clamping,Stage.Lifting,Stage.Transferring,Stage.Lowering,Stage.Releasing,Stage.Complete];
                for (int n=0;n<scans.Length;n++) Check(c.Scan(scans[n]).Stage==expected[n], $"Bad transition {n}");
                Check(c.Scan(new(Start:true)).Stage==Stage.Complete,"Held start restarted");
                c.Scan(new()); Check(c.Scan(new(Start:true)).Stage==Stage.Clamping,"Fresh start failed");
            }),
            ("empty station cannot start", () => Check(new Controller().Scan(new(Start:true,PipePresent:false)).Stage==Stage.Idle,"Started empty")),
            ("all interlocks stop movement", () => {
                Inputs[] faults = [new(EmergencyStop:true),new(GuardClosed:false),new(PressureOk:false),new(CommunicationOk:false)];
                foreach(var input in faults) { var s=Moving().Scan(input); Check(s.Stage==Stage.Fault,"Not faulted"); NoMotion(s); }
            }),
            ("clamp loss stops transfer", () => { var c=Moving(); var s=c.Scan(new()); Check(s.Fault=="Clamp feedback lost","Wrong fault"); NoMotion(s); }),
            ("timeout exact boundary", () => {
                var c=new Controller(300); c.Scan(new(Start:true)); c.Scan(new()); c.Scan(new());
                var s=c.Scan(new()); Check(s.Fault=="Timeout in Clamping","Missing timeout"); NoMotion(s);
            }),
            ("latched fault and deliberate reset", () => {
                var c=Moving(); c.Scan(new(EmergencyStop:true));
                Check(c.Scan(new()).Stage==Stage.Fault,"Auto recovered");
                Check(c.Scan(new(Reset:true,Start:true)).Stage==Stage.Idle,"Reset moved machine");
                Check(c.Scan(new(Start:true)).Stage==Stage.Idle,"Held start moved machine");
                c.Scan(new()); Check(c.Scan(new(Start:true)).Stage==Stage.Clamping,"Cannot restart");
            }),
            ("reset held through unsafe condition requires new edge", () => {
                var c=Moving(); c.Scan(new(EmergencyStop:true,Reset:true));
                Check(c.Scan(new(Reset:true)).Stage==Stage.Fault,"Held reset cleared fault");
                c.Scan(new()); Check(c.Scan(new(Reset:true)).Stage==Stage.Idle,"Fresh reset failed");
            }),
            ("first fault is retained", () => {
                var c=Moving(); c.Scan(new(GuardClosed:false));
                Check(c.Scan(new(EmergencyStop:true)).Fault=="Guard open","First cause overwritten");
            }),
            ("invalid scan does not mutate state", () => {
                var c=Moving(); try { c.Scan(new(),0); throw new Exception("Accepted invalid scan"); }
                catch(ArgumentOutOfRangeException) { Check(c.Stage==Stage.Lifting,"State changed"); }
            }),
            ("four plant scenarios have expected outcomes", () => {
                Check(Simulation.Run("normal")[^1].Result.Stage==Stage.Complete,"Plant did not finish");
                foreach(var scenario in new[]{"guard-open","clamp-loss","actuator-stall"}) {
                    var last=Simulation.Run(scenario)[^1].Result;
                    Check(last.Stage==Stage.Fault,$"Scenario {scenario} did not fault"); NoMotion(last);
                }
                Check(Simulation.Run("actuator-stall")[^1].Result.Fault=="Timeout in Clamping","Wrong stall diagnosis");
            }),
            ("interlocks apply in every state", () => {
                Inputs[] sequence=[new(Start:true),new(ClampClosed:true),new(ClampClosed:true,AtTop:true),
                    new(ClampClosed:true,AtDestination:true),new(ClampClosed:true,AtBottom:true),new(ClampOpen:true)];
                for(int stop=0;stop<=sequence.Length;stop++) {
                    var c=new Controller(); for(int n=0;n<stop;n++) c.Scan(sequence[n]);
                    var s=c.Scan(new(EmergencyStop:true)); Check(s.Stage==Stage.Fault,"Stage ignored E-stop"); NoMotion(s);
                }
            })
        ];
        int failed=0;
        foreach(var (name,test) in tests)
        {
            try { test(); Console.WriteLine($"PASS {name}"); }
            catch(Exception e) { failed++; Console.Error.WriteLine($"FAIL {name}: {e.Message}"); }
        }
        Console.WriteLine($"{tests.Length-failed}/{tests.Length} tests passed");
        return failed==0 ? 0 : 1;
    }
}
