"""Mock data fixtures for testing pipeline offline with zero quota consumption."""

MOCK_RESEARCH_MD = """# Research Dossier: The Quantum Advantage Race (2026 Breakthrough)

## Brief Documentation Summary
In recent developments, quantum computing has entered the utility-scale era, with verifiable benchmarks demonstrating logical qubits operating with quantum error correction far exceeding classical supercomputer capabilities. This documentary traces the turning point from theoretical physics to industrial disruption in material science, pharmaceutical simulation, and national security.

## Key Facts & Timeline
- **2023-2024**: Emergence of neutral-atom and superconducting quantum chips reaching thousands of noisy qubits.
- **2025**: Demonstration of fault-tolerant quantum logical operations by major institutions.
- **2026**: Announcement of real-world pharmaceutical molecular simulations solving enzymes unsolvable on Frontier/Aurora supercomputers.
- Logical error rates reduced by 100x using topological and surface codes.

## Key Players
- **Global Tech Consortia**: Leading computing laboratories deploying neutral-atom and transmon architectures.
- **National Research Institutes**: Government-backed quantum initiatives in the US, Europe, and Asia.
- **Biotech & Material Science Pioneers**: Early enterprise adopters solving molecular bonding equations.

## Current Situation & Analysis
Classical computers struggle exponentially with quantum-mechanical simulations because tracking 300 interacting electrons requires more bits than atoms in the observable universe. Quantum processors exploit superposition and entanglement to model nature natively. While post-quantum cryptography migrations are accelerating, commercial advantage has officially arrived in specific high-value chemical domains.

## What's Next
- Integration of quantum co-processors into hybrid cloud AI architectures.
- Global standardization of post-quantum cryptographic algorithms (NIST standards finalized).
- Transition from specialized experimental labs to commercial cloud availability by 2027.

## SOURCES
1. **Nature Physics Research Archive**: "Fault-tolerant logical qubit operations beyond classical simulation limits" (Published Q1 2026) - Verified.
2. **IEEE Quantum Engineering Review**: "Utility-Scale Quantum Benchmarks in Molecular Dynamics" (Published 2026) - Verified.
3. **NIST Post-Quantum Cryptography Consortium Report**: "Transition Milestones and Standard Adoption Rates" (2026) - Verified.
4. [Unverified Claim Excluded]: Unsubstantiated forum claims regarding proprietary room-temperature quantum room processors were evaluated and marked unverified.
"""

def generate_mock_script(word_count: int = 1520) -> list[dict]:
    """Generate a realistic mock script matching required word count bounds."""
    scenes = [
        {
            "scene_id": "scene_01",
            "scene_title": "The Hook",
            "narration": (
                "Right now, deep inside subterranean research facilities, humanity is unlocking a computational realm "
                "so powerful that our fastest supercomputers appear as simple abacuses by comparison. For decades, "
                "quantum supremacy was dismissed as a distant science fiction fantasy. But in 2026, an undeniable "
                "breakthrough has quietly altered the trajectory of human technology forever. This is not merely an "
                "incremental speed upgrade; it is the genesis of an entirely new physical era."
            ),
            "estimated_duration_seconds": 32,
        },
        {
            "scene_id": "scene_02",
            "scene_title": "Context and The Classical Wall",
            "narration": (
                "To understand why this moment matters, we have to look back at the silicon revolution that powered "
                "the modern world. For sixty years, Moore's Law held true: doubling the density of transistors on microchips "
                "every eighteen months. But physics eventually pushed back. When transistors shrink to the width of a few "
                "atoms, quantum tunneling causes electrical signals to bleed through physical barriers. Classical computation "
                "hit a fundamental thermal and quantum ceiling. Every complex problem in chemistry, materials discovery, and "
                "complex system logistics demanded exponentially more silicon than our planet could power."
            ),
            "estimated_duration_seconds": 45,
        },
        {
            "scene_id": "scene_03",
            "scene_title": "The Quantum Leap: Superposition & Entanglement",
            "narration": (
                "Enter quantum mechanics. Unlike a classical bit, which exists strictly as a zero or a one, a qubit exploits "
                "superposition. It can explore vast multidimensional mathematical probability landscapes simultaneously. Add "
                "entanglement—what Albert Einstein famously called 'spooky action at a distance'—and the processing capability "
                "scales exponentially with every single qubit added. Yet for years, the fatal flaw of quantum systems was noise. "
                "The slightest cosmic ray, microscopic vibration, or thermal flux would collapse the delicate quantum state. "
                "Until researchers finally conquered error correction."
            ),
            "estimated_duration_seconds": 46,
        },
        {
            "scene_id": "scene_04",
            "scene_title": "The Breakthrough of 2026",
            "narration": (
                "The turning point arrived with the development of fault-tolerant logical qubits. By weaving hundreds of noisy "
                "physical qubits into collective mathematical error-correcting codes, scientists reduced computation error rates "
                "by more than two orders of magnitude. For the first time in history, a quantum processor ran a sustained, multi-hour "
                "simulation of complex enzymatic reactions—a calculation that would have consumed ten thousand years on the world's "
                "fastest supercomputer. The race was no longer theoretical; the commercial era of quantum utility had officially begun."
            ),
            "estimated_duration_seconds": 44,
        },
        {
            "scene_id": "scene_05",
            "scene_title": "Geopolitics, Security, and The Encryption Shift",
            "narration": (
                "With unimaginable computing power comes geopolitical tension. Modern cybersecurity relies on mathematical "
                "problems that are virtually impossible for classical computers to reverse-engineer, such as factoring massive prime "
                "numbers. A sufficiently advanced quantum computer running Shor's algorithm could unravel standard RSA encryption in "
                "hours. Consequently, financial institutions, national defense networks, and global infrastructure are rapidly "
                "migrating to post-quantum cryptographic standards approved by international standards bodies. The digital locks of "
                "the twentieth century are being completely replaced."
            ),
            "estimated_duration_seconds": 42,
        },
        {
            "scene_id": "scene_06",
            "scene_title": "What Lies Ahead",
            "narration": (
                "Looking forward, the next five years will see quantum co-processors linked directly to artificial intelligence data "
                "centers. Together, AI and quantum computation will design next-generation battery chemistries, room-temperature "
                "superconductors, and targeted cancer therapeutics with atomic precision. We are standing on the shoreline of an vast "
                "computational ocean, gazing into possibilities that will redefine the boundaries of human knowledge."
            ),
            "estimated_duration_seconds": 38,
        },
        {
            "scene_id": "scene_07",
            "scene_title": "Conclusion and Outro",
            "narration": (
                "As we step into this brave new technological horizon, one question remains: how will humanity wield the power to "
                "compute reality itself? If you enjoyed this investigative documentary, don't forget to hit the like button, subscribe "
                "for weekly deep dives into the technologies shaping our world, and leave a comment below sharing your thoughts on the "
                "quantum revolution. Thank you for watching, and we'll see you in the next episode."
            ),
            "estimated_duration_seconds": 35,
        },
    ]

    # Expand body scenes proportionally across scenes to fulfill exact word count
    total_words = sum(len(s["narration"].split()) for s in scenes)
    fillers = [
        " In addition, material scientists are deploying quantum simulation algorithms to catalog stable crystalline phases previously thought inaccessible. By mapping lattice energy landscapes with atomic precision, labs have synthesized superconducting thin films operating under significantly reduced cryogenic thresholds.",
        " Meanwhile, sovereign wealth funds and defense departments have recognized quantum supremacy as the apex strategic technology of the 21st century. Billions in capital are pouring into specialized fabrication foundries capable of producing coherent optical interconnects at scale.",
        " Furthermore, global industrial consortia are integrating cryogenic control systems directly with standard CMOS semiconductor processes to unlock unprecedented miniaturization. This guarantees that quantum coprocessors will soon augment conventional high-performance computing clusters seamlessly.",
        " The economic reverberations are already rippling through financial clearinghouses, where portfolio risk assessments and derivative valuations that formerly ran overnight are executed in fractions of a second."
    ]
    f_idx = 0
    s_idx = 1
    while total_words < word_count:
        scenes[s_idx % (len(scenes) - 1)]["narration"] += fillers[f_idx % len(fillers)]
        total_words = sum(len(s["narration"].split()) for s in scenes)
        f_idx += 1
        s_idx += 1

    # Recalculate duration for all scenes based on 145 WPM
    for s in scenes:
        w = len(s["narration"].split())
        s["estimated_duration_seconds"] = max(5, int((w / 145) * 60))

    return scenes
