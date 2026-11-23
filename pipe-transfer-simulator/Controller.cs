namespace PipeTransfer;

public enum Stage { Idle, Clamping, Lifting, Transferring, Lowering, Releasing, Complete, Fault }

// One immutable input snapshot per scan; the controller does not read hardware.
public record Inputs(
    bool Start = false, bool Reset = false, bool EmergencyStop = false,
    bool GuardClosed = true, bool PressureOk = true, bool CommunicationOk = true,
    bool PipePresent = true, bool ClampClosed = false, bool AtTop = false,
    bool AtDestination = false, bool AtBottom = false, bool ClampOpen = false);

public record Outputs(bool Clamp, bool Lift, bool Transfer, bool Lower, bool Release);
public record Snapshot(Stage Stage, string? Fault, Outputs Outputs);

public sealed class Controller
{
    public Stage Stage { get; private set; } = Stage.Idle;
    public string? Fault { get; private set; }
    private int elapsedMs;
    private bool previousStart;
    private bool previousReset;
    private readonly int timeoutMs;

    public Controller(int timeoutMs = 5000)
    {
        if (timeoutMs <= 0) throw new ArgumentOutOfRangeException(nameof(timeoutMs));
        this.timeoutMs = timeoutMs;
    }

    public Snapshot Scan(Inputs input, int cycleMs = 100)
    {
        if (cycleMs <= 0 || cycleMs > 1000) throw new ArgumentOutOfRangeException(nameof(cycleMs));
        var startEdge = input.Start && !previousStart;
        var resetEdge = input.Reset && !previousReset;
        previousStart = input.Start;
        previousReset = input.Reset;

        // Priority is deterministic when several interlocks fail in one scan.
        string? unsafeReason = input.EmergencyStop ? "Emergency stop" :
            !input.GuardClosed ? "Guard open" : !input.PressureOk ? "Low pressure" :
            !input.CommunicationOk ? "Communication lost" : null;
        if (unsafeReason is not null) Trip(unsafeReason);
        else if (Stage == Stage.Fault)
        {
            // Clearing the cause alone never resumes movement. Reset returns to Idle.
            if (resetEdge) { Fault = null; Enter(Stage.Idle); }
        }
        else if (Stage is Stage.Idle or Stage.Complete)
        {
            if (startEdge && input.PipePresent) Enter(Stage.Clamping);
        }
        else
        {
            elapsedMs += cycleMs;
            // Clamp feedback must remain true during every transport stage.
            if (Stage is Stage.Lifting or Stage.Transferring or Stage.Lowering && !input.ClampClosed)
                Trip("Clamp feedback lost");
            else if (elapsedMs >= timeoutMs) Trip($"Timeout in {Stage}");
            else
            {
                var next = Stage switch
                {
                    Stage.Clamping when input.ClampClosed => Stage.Lifting,
                    Stage.Lifting when input.AtTop => Stage.Transferring,
                    Stage.Transferring when input.AtDestination => Stage.Lowering,
                    Stage.Lowering when input.AtBottom => Stage.Releasing,
                    Stage.Releasing when input.ClampOpen => Stage.Complete,
                    _ => Stage
                };
                if (next != Stage) Enter(next);
            }
        }
        var hold = Stage is Stage.Clamping or Stage.Lifting or Stage.Transferring or Stage.Lowering;
        return new(Stage, Fault, new(hold, Stage == Stage.Lifting,
            Stage == Stage.Transferring, Stage == Stage.Lowering, Stage == Stage.Releasing));
    }

    private void Enter(Stage stage) { Stage = stage; elapsedMs = 0; }
    private void Trip(string reason) { if (Stage != Stage.Fault) Fault = reason; Enter(Stage.Fault); }
}
