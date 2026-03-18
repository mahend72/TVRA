# O-ETB Sample Use Case Build Guide

The goal is to have simple to follow PoC guide.
Each code section clearly marks what's predefined by O-ETB and what you need to write.

All extra code is at: Internal/WPs/WP3/AssuranceWork/Partners/UoW/
In the zip file the 0-ETB_orig is clean Rance version. 
Rance comments:
```
The O-ETB repository is now available at https://github.com/MedSecurance/Assurance . Please use this GitHub repository as the source for your ongoing efforts to use the Assurance Tool. It is not public but is writeable by all members of the team as the membership is currently defined. If others need to be added please contact Scott Hansen. Please run by me any proposed changes to files in src before committing them. Also refrain from modifying files that are part of distributed examples.
I am working toward eliminating the need for you to modify any of the core (especially src) files. Most contributions and user-provided inputs will be in the KB subdirectory of the repo, rather than in src.
New files/directories may be added under the present KB structure as needed for partner contributions. Do not push to the repo files that represent local experiments in your workspace that may conflict with others. However, such items may be checked in by agreement of multiple partners who are working together on examples.
```

## Issues
- Running with command line options does not work, running from interactive `load_procs('../KB/PROCS/proc_simple.pl').` if fine.
```
./etb --procs "../KB/PROCS/proc_simple.pl"
Argv: ['--procs','../KB/PROCS/proc_simple.pl']
Options=[command(_3630),model(_3654),patterns(_3678),test(false),verbose(true),procs('../KB/PROCS/proc_simple.pl')]
ERROR: -g etb: Unknown procedure: procs:load_procs/2
ERROR:   However, there are definitions for:
ERROR:         procs:load_procs/1
ERROR: 
ERROR: In:
ERROR:   [12] procs:load_procs('../KB/PROCS/proc_simple.pl',_148)
ERROR:   [11] etb:etb_with_opts([command(_194),...|...]) at /Assurance/src/etb.pl:110
ERROR:    [9] etb:etb at /Assurance/src/etb.pl:74
ERROR:    [8] catch(user:etb,error(existence_error(procedure,...),context(...,_290)),'$toplevel':true) at /usr/lib/swi-prolog/boot/init.pl:565
ERROR:    [7] catch_with_backtrace(user:etb,error(existence_error(procedure,...),context(...,_354)),'$toplevel':true) at /usr/lib/swi-prolog/boot/init.pl:645
ERROR: 
ERROR: Note: some frames are missing due to last-call optimization.
ERROR: Re-run your program in debug mode (:- debug.) to get more detail.
```
- etb_reset won't work from BUILD directory
```
make: *** No rule to make target 'clean'.  Stop.
etb_reset : command failed
script aborted
```
- from `src` it will work but throws clean error
```
../BUILD/etb

find -d ../CAP -not \( -name "README.md" -or -name "CAP" -or -path "../CAP/iomt_system_example/*" -or -name "iomt_system_example.txt" -or -name "iomt_system_example" -or -path "../CAP/iso_system_example/*" -or -name "iso_system_example.txt" -or -name "iso_system_example" \) -delete
find: warning: the -d option is deprecated; please use -depth instead, because the latter is a POSIX-compliant feature.
find: paths must precede expression: `../CAP'
find: possible unquoted pattern after predicate `-d'?
make: *** [makefile:15: clean_cap] Error 1
etb_reset : command failed
script aborted

Fixed syntax linux
find ../CAP -depth -not \( -name "README.md" -or -name "CAP" -or -path "../CAP/iomt_system_example/*" -or -name "iomt_system_example.txt" -or -name "iomt_system_example" -or -path "../CAP/iso_system_example/*" -or -name "iso_system_example.txt" -or -name "iso_system_example" \) -delete

find ../REPOSITORY/CASES -depth -not \( -name "README.md" -or -name "CASES" \) -delete
find ../REPOSITORY/EVIDENCE -depth -not \( -name "README.md" -or -name "EVIDENCE" -or -name "axiom" -or -name "certificate" -or -name "iomtmodeling" -or -name "ichecker" -or -name "ocra" -or -name "unknown" \) -delete
```
- `etb_reset` kind of work when it's at the end of procedure and you still have to quit etb and re-run the workflow

## Questions
- Can we have a list of conventions that we do have to adher to to make sure the code is loaded automaticly, e.g. `_validate, pattern_` etc ?
- In order to integrate with other tools we need some API to call ETB probably from the front-end, will there be an option to upload additional patterns/files to ETB running in the container?
- How can you call ETB so it does run and then quit. At the moment when you run `./etb -c "proc(demo)" the code stays in the console? 


- How you enable Debug mode, what are the other verbose modes for troubleshooting, e.g.
```
Argv: []
Options=[command(_3224),model(_3248),patterns(_3272),procs(_3296),test(false),verbose(true)]
command_mode=etb user_level=developer etb_mode=normal
test=off regression_test=off initialize=on verbose=on
```
Rance comments:
```
The above 4 lines were primarily for my use while testing command line options.
There are flags to signal verbose mode, but it is not well developed in the code. Generation of (more) verbose output can be implemented as it provides general utility.
```
- How do you make instatianting_pattern verbose to see variables used, what's called why something is not called.
Rance comments:
```
There is currently no code providing verbose visibility of pattern instantiation, only the console messages when instantiation is started and when it is completed. There are only a few error conditions detected during instantiation that accumulate in a log for the instantiation that is stored in the persistent store for the generated assurance case but the logs are incomplete and their application is undeveloped.
```
- CaseId numbers, assurance Xref how I know which number is next.
```
CaseIds are atomic tokens chosen by the user. Instance ids for AC elements are generated when each new element is inserted in its CASES repo using a counter that is maintained and incremented there.
```

- The proc(stm_inst) only calls temp_test_validate once. When I rerun proc(stm_inst) the temp_test_agent.pl is not executed.
Rance comments:
```
After the first run the evidence record already exists in the database.
The instantiate module before inserting a new evidence record for a given category, claim and context (with the current actual arguments) always checks whether the record already exists and it only does the insert and validate if it doesn't already exist. An agent may asynchronously change the status file for the evidence record.
There is an ETB command "update" that causes ETB to search the EVIDENCE repo for a status file change and when it finds a change to valid or invalid it updates the evidence record.
While you are testing, standard practice should be to clean the appropriate areas of the database (using one of the modes of the ETB etb_reset command or the makefile targets).
When you do want to run an example that needs the repository to carry forward its state between runs of the tool then it is appropriate to run the update command on the subsequent runs to be sure that the database reflects status changes that may have been registered by agents since the records were created or the last update was run.
```
Summary: 
  - Use `update` command if requires re-run.
  - Use `etb_reset` for clean re-run.
  - Depending on the scenerio you can add either at the top of your proc procedure.


- Do naming convetion matter, I have to manually call from proc_etb.pl `load_patterns('../KB/PATTERNS/stm_patterns.pl'),`
Rance comments:
```
The load_patterns command, as you have written it, will work when you start ETB from src. It will also work if you start it from BUILD, but currently some other things won't work, such as auto-loading of the standard agents from src/agents. I am fixing this issue as I am also moving the agents from src/agents to KB/AGENTS. This is in keeping with the objective of having user contributed files in KB rather than src.
Further, on the subject of conventions, it was the case that there was a convention for the names of patterns files, namely, that the file names in the PATTERNS directory had the prefix 'patterns_'. In my latest commit I am removing this convention. The example files that are already there (patterns_MILS.pl, patterns_IoMT.pl and patterns_ISO_81001.pl) continue to have the same name but the code has been changed to not require the convention, and where these files are identified in src/com/param.pl their full names are used (minus the .pl extension).
Also note that in the load_patterns command you need not include the .pl extension on the file name.
With the most recent changes the .pl extension is superfluous both in the command and the file name.
That is, your file could be called just '../KB/PATTERNS/stm_patterns'.
The command load_patterns('../KB/PATTERNS/stm_patterns') will load the file whether or not the file name has the .pl extension. What WON'T work is the command load_patterns('../KB/PATTERNS/stm_patterns.pl') when the actual file does not have the .pl extension.
This will return a console message that the file could not be found and the command will fail.

The preceding explanation also applies to the command load_procs and the files that it loads.
The situation is a little different with respect to agent files, because agents are Prolog modules and their actual file names must end in .pl. (I haven't tested these without .pl but I believe it to be the case.)
To summarize: for files with proc definitions and ac pattern definitions, there is not restriction on the file name, and it may have a .pl extension or not.
```
Summary:
  - When using `load_patterns` include full extension, e.g. `tvra_patterns.pl`
  - There is ongoing work to move user code into `KB/` folders to avoid changing core `src`
  - It's better to keep `.pl` extension on the files


## Things I've learn
### Prolog Naming Conventions (`proc` Example)

When exploring O-ETB's source code, particularly files like `src/procs_etb.pl`, you'll encounter specific Prolog conventions. For example, you might see procedure definitions like:

```prolog
proc(person_inst, [...]).
proc('IoMT_case', [...]).
```

These `proc/2` predicates define named sequences of O-ETB commands, acting like reusable macros or procedures. They bundle multiple `etb` tool commands together, which can then be executed simply by typing `etb> proc(person_inst).` or `etb> proc('IoMT_case').` in the interactive tool.

**Why the quotes?** The use of single quotes (`' '`) around `'IoMT_case'` but not `person_inst` follows standard Prolog rules for **atoms** (symbolic names):

*   Atoms starting with a **lowercase letter** (e.g., `person_inst`) and containing only letters, numbers, and underscores can be written directly.
*   Atoms starting with an **uppercase letter** (e.g., `IoMT_case`) *must* be enclosed in single quotes to distinguish them from variables. Atoms containing other characters (like hyphens or spaces) also require quotes.

Keep this convention in mind when reading or writing Prolog code within O-ETB.
**The O-ETB User Manual section 1.2.4 discusses the lexicographic/syntactic conventions that apply to the O-ETB commands and to entries in the O-ETB knowledge base.**

### Understanding `src/command_etb.pl`

While `src/procs_etb.pl` defines reusable *sequences* of commands (macros), the file `src/command_etb.pl` defines the **individual interactive commands** themselves (like `instantiate_pattern_list`, `export_case`, `load_model_v`, etc.).

This file specifies:

*   **Syntax**: The command name and the arguments it expects.
*   **Semantics**: Rules to validate the arguments you provide.
*   **Help**: The text displayed when you run `help(command_name)`.
*   **Execution (`do`)**: The actual Prolog code that runs when you enter the command, connecting the command you type to the underlying O-ETB functions.

Essentially, `command_etb.pl` provides the building blocks (the vocabulary) for the `etb` tool, while `procs_etb.pl` uses these blocks to create convenient workflows.
Rance comments:
```
Your description is accurate. While it is envisioned that users will want to define their own procs defined in proc files outside of the src directory, it is not as likely that users will define new etb commands. I would entertain requests for new commands to be provided if necessary, but would not encourage users to make such extensions for consistency and compatibility because implementing etb commands in most cases involves interacting with internal functions and data structures. 
```

### Handling Non-System Elements (e.g., `person`)

You might notice that some procedures, like `person_inst` found in `src/procs_etb.pl`, instantiate patterns for concepts like `'person'` without referencing a detailed system model like `stm_model.pl`:

```prolog
proc(person_inst, [
    instantiate_pattern('person', ['Marius', 'Programming'], 'person_examp'),
    export_case(cap_person,txt),
	detach_case
]).
```

This is because not all elements in an assurance case represent technical system components. Concepts like personnel roles, organizational policies, or specific documents are often defined directly as **Assurance Case Patterns (`ac_pattern`)** within the `KB/PATTERNS/` directory.

Instead of a `model_spec`, the pattern definition for `'person'` itself contains the necessary structure:

*   **Arguments**: It defines what information is needed (e.g., a name and a role).
*   **Goal Structure**: It provides a predefined template of goals, context, and evidence placeholders related to that concept (e.g., asserting the person's role and linking to evidence like a CV).

The `instantiate_pattern('person', ['Marius', 'Programming'], 'person_examp')` command then works by:
1. Finding the `ac_pattern` definition for `'person'`.
2. Substituting the provided arguments (`'Marius'`, `'Programming'`) into the pattern's template placeholders.
3. Creating a concrete assurance case fragment (named `'person_examp'`) based on this filled-in template.

So, the "building blocks" for elements like `person` come directly from their `ac_pattern` definition, not from a separate system model file.

### How Assurance Cases are Exported (`export_case`)

When you use a command like `export_case(some_name, html)` or `export_case(another_name, txt)` in the `etb` tool or within a `proc` definition, you're triggering the export process.

Here's how it works behind the scenes:

1.  **Command Recognition**: The `etb` tool recognizes the `export_case` command and its arguments (base name and format) based on the definitions in `src/command_etb.pl`.
2.  **Delegation**: The actual work isn't done directly in `command_etb.pl`. Instead, the `do(export_case(Name,Format))` rule delegates the task by calling `export:ac_export(Name, Format)`.
3.  **`src/export.pl` Logic**: This call invokes the `ac_export/2` predicate defined within the `src/export.pl` module. This module contains the core logic for generating the output.
4.  **Format Handling**: Inside `ac_export/2`, the code checks the `Format` argument (`txt` or `html`). Based on this value, it executes different internal logic to traverse the structure of the currently active assurance case and generate the corresponding output format.
5.  **Output Destination**: The generated files (either a single `.txt` file or a set of `.html` files for the web view) are saved within the `CAP` (Certification Assurance Package) directory, using the `Name` argument you provided as the base filename or directory name.

So, while `command_etb.pl` defines the command *interface*, `export.pl` holds the *implementation* for transforming the internal assurance case representation into the desired output format.
Rance comments:
```
For the export_case command. Other commands in command_etb.pl are implemented in different modules. The command module provides the ETB command line interfaces to various functions.
```

### Breakdown of mils_system_inst
The commands are defined in `src/command_etb.pl`
```prolog
proc(mils_system_inst, [ % Defines a procedure named 'mils_system_inst'
	set_v(ModelId, '1.0'),
        % set_v/2: Sets an internal O-ETB variable.
        % Here, it sets the variable 'ModelId' to the atom '1.0'.
        % This likely tells subsequent commands which model version to use from KB/MODELS/.

	set_v(CaseId, mils_system_example),
        % set_v/2: Sets another internal variable.
        % 'CaseId' is set to the atom 'mils_system_example'.
        % This name will be used to identify the assurance case being constructed.

	load_model_v(ModelId, Policy, Platform, _Configuration),
        % load_model_v/4: Loads a system model from the Knowledge Base (KB).
        % It uses the value currently stored in the 'ModelId' variable ('1.0') to find the model.
        % It then parses the model and binds parts of it to Prolog variables:
        %   - Policy: Captures the application/policy architecture details.
        %   - Platform: Captures the platform/hardware details.
        %   - _Configuration: Captures configuration details (underscore indicates the value might not be used further in *this* proc).
        % These Prolog variables (Policy, Platform) are now available for use in subsequent commands within this proc execution.

	set_v(AC, % Sets the variable 'AC' to a list structure for pattern instantiation.
		[ 'foundational_plane'-[Platform], % Pair 1: Pattern 'foundational_plane' with argument [Platform] (the variable bound by load_model_v)
		  'operational_plane'-[Policy],     % Pair 2: Pattern 'operational_plane' with argument [Policy] (the variable bound by load_model_v)
		  'person'-['Alice', 'AC Patterns Definition'], % Pair 3: Pattern 'person' with arguments 'Alice' and 'AC Patterns Definition'
		  'person'-['Bob', 'ETB Development']           % Pair 4: Pattern 'person' again, with different arguments
		]),
        % set_v/2: Sets the internal variable 'AC' to a specific Prolog list.
        % This list defines which assurance case patterns to instantiate and what arguments to pass to them.
        % It uses the 'PatternName - ArgumentList' syntax. Crucially, it uses the Prolog variables 'Platform' and 'Policy'
        % that were bound by the `load_model_v` command earlier.

	instantiate_pattern_list(AC,CaseId),
        % instantiate_pattern_list/2: Instantiates a list of patterns into an assurance case.
        % It takes the list stored in the variable 'AC' and the case identifier from the variable 'CaseId' ('mils_system_example').
        % It iterates through the list in 'AC', finds each pattern ('foundational_plane', 'operational_plane', 'person', 'person')
        % in the KB/PATTERNS directory, and instantiates them using the provided arguments (including the model data from 'Platform' and 'Policy').
        % The resulting instantiated assurance case fragments are added to the case named 'mils_system_example' in the REPOSITORY/CASES.

	export_case(CaseId,html),
        % export_case/2 (or ac_export/2): Exports the assurance case.
        % It takes the case identifier from the 'CaseId' variable ('mils_system_example') and the format 'html'.
        % It generates an HTML representation of the assurance case 'mils_system_example' and saves it into the CAP directory.
        % (See O-ETB User Manual Sec 4.9.4 & 5.2.2).

	detach_case
        % detach_case/0: Detaches the currently active assurance case.
        % This cleans up the O-ETB internal state related to the case, potentially saving any final changes
        % from the working cache to persistent storage (REPOSITORY/CASES) and clearing the cache.
        % (See O-ETB User Manual Sec 4.6.3).
]).
```

### Breakdown of simple pattern case

The simple pattern case demonstrates a minimal example of an O-ETB assurance case with evidence validation. Let's break down each component:

```prolog
proc(simple, [ % Defines a procedure named 'simple'
    % Load the pattern
    load_patterns('/Assurance/KB/PATTERNS/pattern_simple.pl'),
        % load_patterns/1: Loads pattern definitions from the specified file.
        % This makes the 'simple_threat_analysis' pattern available for instantiation.

    update,
        % update/0: Refreshes evidence status in the repository.
        % This ensures any evidence status changes are reflected in the assurance case.

    % Set variables
    set_v(CaseId, simple_case),
        % set_v/2: Sets an internal O-ETB variable.
        % Here, it sets 'CaseId' to the atom 'simple_case'.
        % This is the identifier for our assurance case.

    set_v(SystemName, 'simple_system'),
        % set_v/2: Sets another internal variable.
        % 'SystemName' is set to 'simple_system'.
        % This will be substituted into the pattern during instantiation.

    % Instantiate the pattern
    instantiate_pattern('simple_threat_analysis', [SystemName], CaseId),
        % instantiate_pattern/3: Creates an instance of a pattern.
        % It takes:
        %   - The pattern name: 'simple_threat_analysis'
        %   - A list of arguments: [SystemName] (the variable we set above)
        %   - The case ID: CaseId (the variable we set above)
        % This creates an assurance case instance with the pattern structure.

    % Export the case
    % export_case(CaseId, html),
        % This line is commented out but would export the case in HTML format.
        % When uncommented, it would generate HTML files for the assurance case.

    % Cleanup
    detach_case,
        % detach_case/0: Releases the current assurance case from memory.
        % This ensures the case is saved to the repository and memory is freed.

    etb_reset
        % etb_reset/0: Resets the ETB environment.
        % This cleans up resources and prepares for the next run.
]).
```

The pattern being instantiated is defined in `pattern_simple.pl`:

```prolog
ac_pattern('simple_threat_analysis',
    [arg('SystemName', system:name)],
    goal('G1', 
        'System {SystemName} is secure',
        [],
        [evidence(simple_threat, 'Threat analysis for {SystemName}', [])]
    )
).
```

This pattern defines:
- Name: 'simple_threat_analysis'
- Parameters: A single parameter 'SystemName' of type system:name
- Structure: A goal claiming the system is secure, with a piece of evidence

The evidence validation is handled by:

1. Category definition in `categories.pl`:
```prolog
evidence_category(simple_threat, 'Simple threat evidence', security_evidence, simple_threat_check).
validation_method(simple_threat_check, 'Simple validation', simple_agent).
validation_agent(simple_agent, [], []).
```

2. The validation agent in `simple_agent.pl`:
```prolog
:- module(simple_agent, [simple_threat_validate/5]).

simple_threat_validate(_Claim, _Context, _Args, _XRef, Status) :-
    format('~n*** Starting Simple Threat Validation Agent for: ~w', [XRef]),
    format(atom(Command), 'python3 /Assurance/KB/AGENTS/simple_gateway.py', []),
    % Call the Python script with error handling
    (   shell(Command, ResultCode)
    ->  (   ResultCode = 0
        ->  format('~n*** Python script executed successfully', []),
            % Read the result from the JSON file
            (   exists_file('/Assurance/KB/AGENTS/simple_result.txt')
            ->  open('/Assurance/KB/AGENTS/simple_result.txt', read, Stream),
                read_string(Stream, _, ResultString),
                close(Stream),
                % Remove quotes from JSON string if present
                (   sub_atom(ResultString, 0, 1, _, '"'),
                    sub_atom(ResultString, _, 1, 0, '"')
                ->  sub_atom(ResultString, 1, _, 1, CleanResult)
                ;   CleanResult = ResultString
                ),
                % Set the Status based on the result
                atom_string(Status, CleanResult),
                format('~n*** Simple Threat Validation Result: ~w ', [Status])
            ;   format('~n*** Error: simple_result.txt not found', []),
                Status = error
            )
        ;   format('~n*** Python script failed with code ~w', [ResultCode]),
            Status = error
        )
    ;   format('~n*** Error: Failed to execute Python script', []),
        Status = error
    ),
    !.
```

The agent calls a Python script (`simple_gateway.py`) which:
1. Uploads a test file to centralDB
2. Downloads it back
3. Writes the result to `simple_result.txt`
4. Returns a status (typically "valid")

The complete execution flow:

1. When `proc(simple)` is run:
   - The pattern definition is loaded
   - Variables are set for the case name and system name
   - The pattern is instantiated with these variables
   - During instantiation, the evidence validation is triggered
   - The agent calls the Python gateway
   - The Python gateway interacts with centralDB
   - The validation result is returned through simple_result.txt
   - The assurance case is updated with the validation status
   - The case is detached and ETB is reset

#### My workflow:
- Start Assurance container `docker run -d -p 8080:8080 -v ./Assurance:/Assurance --name o-etb o-etb`
- Start centralDB container `docker run -d -p 9000:9000 -v ./local_data:/app/data --name o-etb-evidence o-etb-evidence-mgmt`
- copy user files to container `cp -r KB build/Assurance/`
- Enter container `docker exec -t -i o-etb /bin/bash`
- In container copy makefile where we fix `etb_reset`, e.g. `cp /Assurance/KB/makefile /Assurance/src/`
- You don't have to run new `make` unless you want to reset ETB
- Start `etb` from `src` directory, e.g. `../BUILD/etb` the reason why is so etb_reset does work
- Load pattern, currently starting `etb --procs` does not work. `load_procs('../KB/PROCS/proc_simple.pl').`
- Call proc, `proc(simple).`
- If you make any changes to the code, copy them from local system to container via mapped folder and remember to `quit.` existing interactive session and start over.


## Implementing the Simple Temperature Monitor (STM) Assurance Case

This section provides a comprehensive, step-by-step guide to creating and running a complete assurance case for the Simple Temperature Monitor (STM) example. I'll explain each component, its purpose, and how everything fits together to create a fully functional O-ETB assurance case.

### Step 1: Complete Repository Structure and Files

Here's the **COMPLETE** directory structure you need to implement:
Rance comments about MODELS versioning:
```
The models already defined, that is the model IDs '1.0' and '2.0' are already taken. 1.0 is used in the MILS system example and 2.0 is one that I'm personally working with for a new example.
I suggest that you make a new directory under MODELS, maybe with a more descriptive name than '1.0' or '2.0' and place your model work there so we don't step on each others' toes.
Any number of such model directories could be created for independent work.
```

```
O-ETB/
├── KB/
│   ├── MODELS/
│   │   └── 2.0/                         
│   │       └── stm_model.pl              <-- System model
│   │   
│   ├── PATTERNS/
│   │   └── stm_patterns.pl               <-- Assurance case patterns. Rance: For now use patters_stm.pl in the future it won't matter.
│   └── EVIDENCE/
│       └── categories.pl                 <-- Evidence category definitions
├── src/
│   ├── agents/
│   │   ├── temp_test_agent.pl            <-- Temperature test validation agent
│   │   ├── doc_agent.pl                  <-- Documentation validation agent
│   │   └── test_agent.pl                 <-- Test report validation agent
│   ├── etb.pl                            <-- Main ETB file (with agent module declarations) Rance: No longer in etb.pl. Agents declared in KB/EVIDENCE/categories.pl are dynamically loaded at init time
│   ├── procs_etb.pl                      <-- Where we'll add our procedure. Rance: Please reserve this file for system use. Users should create their own procs file(s) and load_procs(file)
│   └── makefile                          <-- Build file (optional to update). Rance: I hope to eliminate all need to modify this file. User provided files are not dependencies of the system.
└── REPOSITORY/
    └── EVIDENCE/
        ├── temp_test/
        │   └── 00001                     <-- Temperature test evidence file
        ├── hazard_log/
        │   └── 00001                     <-- Hazard log evidence file
        └── test_report/
            └── 00001                     <-- Test report evidence file
```

### Step 2: Implementing the Automated Procedure

We'll create a custom procedure in `src/procs_etb.pl` to automate the entire process of building and exporting our STM assurance case. This will give us a one-command solution to generate the complete case. Add this procedure to `src/procs_etb.pl`:
Rance comments:
```
Please see comment above about procs files. Note that a loaded procs file may contain :- include(file) directives so that you can load one procs file (using either the interactive command or the --procs command line option to load this file which in turn can include other procs file in the same format.
This should not be a big change for you and avoids editing another file in src/
```
Summary:
  - You should use `--procs` or `load_proc` to load your own procs at runtime and avoid modifing `/src`
  - Same goes for patterns use `--patters` or `load_patterns`

```prolog
% instantiate the STM example using model 2.0 and export
proc(stm_inst, [
	set_v(ModelId, '2.0'), % Use model version 2.0
	set_v(CaseId, stm_system_example), % Name the assurance case
	% First ensure the pattern file is loaded
	load_patterns('../KB/PATTERNS/stm_patterns.pl'),
	% Load the model but use only what's needed
	load_model_v(ModelId, Policy, _Platform, _Configuration),
	% Extract the system name from the policy structure or use a fixed name
	% In this case, we'll use the policy name directly from the loaded structure
	set_v(SystemName, 'stm_system'),
	set_v(AC,
		[ 'stm_safety'-[SystemName], % Use the system name, not the full policy structure
		  'person'-['Alicia', 'Assurance'],
		  'person'-['Roberto', 'Development']
		]),
	instantiate_pattern_list(AC, CaseId),
	export_case(CaseId, txt),
	export_case(CaseId, html),
	detach_case
]).
```

**Detailed explanation of each command:**

1. `set_v(ModelId, '2.0')`: 
   - Sets a variable named `ModelId` with the value `'2.0'`
   - This refers to the model version in `KB/MODELS/2.0/`
   - Critical for O-ETB to locate our STM model

2. `set_v(CaseId, stm_system_example)`: 
   - Creates a variable `CaseId` with the value `stm_system_example`
   - This will be the identifier for our assurance case
   - Used for storage in REPOSITORY/CASES/ and for export filenames

3. `load_patterns('../KB/PATTERNS/stm_patterns.pl')`:
   - Explicitly loads our STM pattern definitions
   - **IMPORTANT**: This ensures our patterns are accessible before instantiating
   - Prevents "pattern not found" errors that can occur if patterns aren't loaded

4. `load_model_v(ModelId, Policy, _Platform, _Coinfiguration)`:
   - Loads the model specified by `ModelId` (2.0)
   - Binds `Policy` to the system architecture from `stm_model.pl`
   - The underscore variables (`_Platform`, `_Configuration`) indicate we're capturing but not using these parts
   - Note: Variables with underscores can still be used, but it's a convention to mark them as potentially unused

5. `set_v(SystemName, 'stm_system')`:
   - Creates a variable `SystemName` with the value `'stm_system'`
   - This matches the pattern's expectation that we'll pass a simple system name
   - **CRITICAL INSIGHT**: The `stm_safety` pattern expects a system name, not a complex structure

6. `set_v(AC, [...])`:
   - Creates an `AC` variable containing pattern-argument pairs
   - Format: `'pattern_name'-[arg1, arg2, ...]`
   - Our list contains:
     - The main `'stm_safety'` pattern with the system name
     - Two instances of the `'person'` pattern with different names and roles

7. `instantiate_pattern_list(AC, CaseId)`:
   - Takes our pattern list (AC) and builds the assurance case
   - Each pattern is instantiated with its arguments
   - The results are stored under our case ID (`stm_system_example`)

8. `export_case(CaseId, txt)` and `export_case(CaseId, html)`:
   - Exports the case in both text and HTML formats
   - Uses the case ID (`stm_system_example`) as the base filename
   - Creates files in the CAP directory for review

9. `detach_case`:
   - Final cleanup step
   - Releases memory and prevents resource leaks
   - Ensures changes are saved to the repository

### Step 3: Creating the Evidence Validation Agents

For O-ETB to validate our evidence, we need to create three agent files:

#### 1. `src/agents/doc_agent.pl` - For Hazard Log Documentation Validation:

```prolog
% PROLOG MODULE DECLARATION - REQUIRED
:- module(doc_agent, [hazard_log_validate/5]).

% Validation agent for hazard documentation
% hazard_log_validate/5 - validates hazard documentation evidence
hazard_log_validate(_Claim, _Context, _Args, XRef, Status) :-
    % Get the evidence record location
    atomic_list_concat(['REPOSITORY/EVIDENCE/hazard_log/', XRef], EvidenceFile),
    
    % Check if evidence file exists - in a real system, you would 
    % perform more thorough validation of the documentation content
    (exists_file(EvidenceFile) ->
        % For this example, we assume any existing file is valid
        Status = 'valid'
    ;
        % File not found - mark as pending to indicate need for evidence
        Status = 'pending'
    ).

% Fallback for any errors
hazard_log_validate(_, _, _, _, 'ongoing').
```
Rance comments:
```
It would be appropriate to use 'ongoing' because even through there is no final verdict the agent indicates that it has taken responsibility from ETB which uses 'pending' until the agent takes over. Status remains as 'pending' if no agent has taken over.
Don't do this anymore. See earlier comments. Just edit the KB/EVIDENCE/categories.pl file and the declared agents will be automatically loaded from KB/AGENTS on initialization.
```
Summary:
  - Use `pending` before agent is called, `onging` once agent is called
  - For agents edit the `KB/EVIDENCE/categories.pl` file and the declared agents will be automatically loaded from KB/AGENTS on initialization.

**Why this implementation works:**
- Module name `doc_agent` precisely matches the agent specified in the `validation_method` declaration in `categories.pl`
- Predicate name `hazard_log_validate/5` follows the naming pattern of Evidence Category + "validate"
- Simply checks for the existence of the evidence file and marks it as valid if found
- Uses a 'pending' status to indicate missing evidence rather than 'invalid' for a cleaner display

#### 2. `src/agents/temp_test_agent.pl` - For Temperature Test Results Validation:

```prolog
% PROLOG MODULE DECLARATION - REQUIRED
:- module(temp_test_agent, [temp_test_validate/5]).

% PREDEFINED O-ETB AGENT INTERFACE: temp_test_validate/5
% Validates temperature test evidence
temp_test_validate(_Claim, _Context, _Args, XRef, Status) :-
    % Get the evidence record location
    atomic_list_concat(['REPOSITORY/EVIDENCE/temp_test/', XRef], EvidenceFile),
    
    % Check if evidence file exists
    (exists_file(EvidenceFile) ->
        % Read the first line of the file to determine status
        open(EvidenceFile, read, Stream),
        read_line_to_codes(Stream, Codes),
        close(Stream),
        atom_codes(FirstLine, Codes),
        
        % Check if it contains the success criteria
        (sub_atom(FirstLine, _, _, _, 'PASS') ->
            Status = 'valid'  % If the file contains PASS
        ;
            Status = 'invalid'  % If the file doesn't contain PASS
        )
    ;
        % File not found - mark as pending
        Status = 'pending'
    ).

% Fallback for any errors
temp_test_validate(_, _, _, _, 'ongoing').
```

**More sophisticated validation:**
- Opens and reads the evidence file to look for "PASS" text
- Demonstrates intelligent evidence validation beyond simple existence checks
- Shows how you might evaluate the content of evidence

#### 3. `src/agents/test_agent.pl` - For Test Report Validation:

```prolog
% PROLOG MODULE DECLARATION - REQUIRED
:- module(test_agent, [test_report_validate/5]).

% Validation agent for test reports
% test_report_validate/5 - validates test report evidence
test_report_validate(_Claim, _Context, _Args, XRef, Status) :-
    % Get the evidence record location
    atomic_list_concat(['REPOSITORY/EVIDENCE/test_report/', XRef], EvidenceFile),
    
    % Check if evidence file exists - in a real system, you would 
    % perform more thorough validation of the test report contents
    (exists_file(EvidenceFile) ->
        % For this example, we assume any existing file is valid
        Status = 'valid'
    ;
        % File not found - mark as pending to indicate need for evidence
        Status = 'pending'
    ).

% Fallback for any errors
test_report_validate(_, _, _, _, 'ongoing').
```

### Step 4: Updating `etb.pl` to Load the Agents

For O-ETB to find and use our agents, they must be explicitly loaded in `src/etb.pl`. Add these lines after the existing agent module declarations:

```prolog
% Agents for STM assurance case
:- use_module(agents/doc_agent).
:- use_module(agents/temp_test_agent).
:- use_module(agents/test_agent).
```

**Why this is critical:**
- Each agent must be explicitly loaded or O-ETB won't find them
- These declarations tell the Prolog system to load our modules
- Without this, you'll get "Unknown procedure" errors during validation
- This is exactly analogous to how the system loads other modules

### Step 5: Creating the Evidence Files

Create three directories and add sample evidence files:

#### 1. `REPOSITORY/EVIDENCE/temp_test/00001`:
Rance comments:
```
I would suggest a different naming convention for evidence auxiliary files.
While the starting value for system-assigned evidence identifiers is currently a five-digit number 10000 (established in src/com/param.pl), it could be set to something else (like 00000) which may conflict with this choice of names. I'd suggest something like 'aux_XXXXX' to create a distinct namespace for the auxiliary files. Or even naming unique to, or constructed from, the evidence category, e.g. 'tt_XXXXX' or 'temp_test_XXXXX'.
```

```
# Temperature Accuracy Test Results
PASS: Temperature accuracy within ±0.1°C

Test Date: 2023-11-20
Test Equipment: Calibrated Reference Thermometer RT-2000
Tester: J. Smith

Test Results:
-------------
Reference: 36.5°C, STM Reading: 36.55°C, Deviation: 0.05°C
Reference: 37.0°C, STM Reading: 37.05°C, Deviation: 0.05°C
Reference: 38.5°C, STM Reading: 38.52°C, Deviation: 0.02°C
Reference: 39.2°C, STM Reading: 39.16°C, Deviation: 0.04°C
Reference: 40.0°C, STM Reading: 40.05°C, Deviation: 0.05°C

All measurements within required tolerance of ±0.1°C
```

**Note the "PASS" at the beginning** - our agent specifically looks for this!

#### 2. `REPOSITORY/EVIDENCE/hazard_log/00001`:

```
# Hazard Log: TemperatureReadingError

Hazard ID: H-001
Hazard Name: TemperatureReadingError
Description: Temperature sensor provides incorrect reading
Severity: Major
Likelihood: Possible
Harm: Incorrect treatment based on false temperature readings

Risk Assessment:
---------------
Initial Risk: Medium (Major severity, Possible likelihood)

Mitigation Measures:
1. Regular sensor calibration
2. Use of medical-grade sensors with high accuracy
3. Software plausibility checks for outlier readings
4. Visual alert for user when readings are outside normal range

Residual Risk After Mitigation: Low

Verification:
------------
Testing completed per Test ID: T-001, T-002
Results: All mitigations verified and effective
```

#### 3. `REPOSITORY/EVIDENCE/test_report/00001`:

```
# Test Report: Mitigation Verification

Test ID: T-001
Test Name: Temperature Sensor Calibration Verification
Date: 2023-11-25
Tester: R. Johnson

Test Description:
----------------
Verify that the temperature sensor calibration procedure effectively limits measurement error.

Test Steps:
1. Calibrate sensor according to documented procedure
2. Take 50 measurements at reference temperatures between 35.0°C and 41.0°C
3. Compare with calibrated reference thermometer

Results:
-------
- All calibrated sensors remained within ±0.1°C of reference readings
- Maximum observed deviation: 0.08°C
- No false positives or false negatives for fever detection threshold

Conclusion:
----------
The calibration procedure effectively mitigates the risk of inaccurate temperature readings.
TEST PASSED
```

### Step 6: Updating the Makefile (Optional)

For maximum flexibility, you can update the `src/makefile` to automatically find all agent files and pattern files without explicitly listing them. This isn't strictly necessary but makes future maintenance easier:
Rance comments:
```
Until we make some of the agents and patterns produced on the project part of the distribution I'd prefer not to do these modification to the makefile. The user provided files are not part of the system and you can have them in your private workspaces. By not prematurely making them part of the system distribution we can avoid conflict among parallel efforts. Recall that the proc and ac_pattern namespaces are global.

At least, I'd prefer that you not check in any makefile changes to the repository.

As explained elsewhere, the system itself does not automatically include all pattern files but only those that are loaded. This is to permit multiple or alternative versions of files that may define the same pattern names.
```
Summary:
  - You should load your User from `KB` and the `proc` can have a `load_patterns` command or use `--patterns` to add aditional code

```makefile
etb:	$(wildcard agents/*.pl) \
	com/command.pl com/param.pl com/procs.pl com/test.pl com/ui.pl \
	models_api/common.pl models_api/configuration.pl models_api/model.pl models_api/platform.pl models_api/policy.pl \
	$(wildcard ../KB/PATTERNS/*.pl) \
	agent_interface.pl assurance.pl command_etb.pl etb_server.pl etb.pl evidence.pl export.pl instantiate.pl kb.pl \
	patterns.pl procs_etb.pl stringutil.pl
	swipl -v -o ../BUILD/etb -g etb -c etb.pl
```

The key changes:
- `$(wildcard agents/*.pl)` - Automatically includes all agent files in the `agents/` directory
- `$(wildcard ../KB/PATTERNS/*.pl)` - Automatically includes all pattern files

This means when you add new agents or patterns, the makefile automatically picks them up without needing changes.

## Running the STM Assurance Case Example

There are two main ways to run our STM example:

### Method 1: Using the Interactive ETB Tool

1. **Start O-ETB in interactive mode**:
   ```bash
   ../BUILD/etb
   ```
Rance comments:
```
From src you can just start in Prolog like this:
    % swipl
    ?- [etb].
    ?-  etb.
    etb>

This approach to starting ETB may avoid some problems with etb command history and debugging.
However it does deprive you of the opportunity of using the --procs, --patterns and --model preload command line options.
```

2. **Run our procedure**:
   ```
   etb> proc(stm_inst).
   ```
   This executes our entire defined workflow at once.

3. **Run with step-by-step execution**:
   ```
   etb> proc(stm_inst, step).
   ```
   This runs the procedure in step-by-step mode, pausing after each command. This allows you to:
   - See each command as it's about to execute (press ENTER to proceed)
   - Examine variables and state between steps
   - Understand the execution flow
   - Debug issues more effectively

   **EXTREMELY USEFUL FOR LEARNING**: This mode shows exactly what's happening at each step and lets you see the internal values and transformations.

   You can also run it directly with the `-c` command line option:
   ```bash
   ./BUILD/etb -c "proc(stm_inst)."
   ```
   
   Or in step mode:
   ```bash
   ./BUILD/etb -c "proc(stm_inst,step)."
   ```

### Understanding the Output

After running `proc(stm_inst)`, you should see output like:

```
*** loading patterns from file ../KB/PATTERNS/stm_patterns.pl ... done.
*** instantiating pattern stm_safety ... done.
*** instantiating pattern hazard_mitigated ... done.
*** instantiating pattern hazard_mitigated ... done.
*** instantiating pattern person ... done.
*** instantiating pattern person ... done.
Exported to CAP/stm_system_example.txt
Exported to CAP/stm_system_example/index.html
```

This means:
1. The patterns were successfully loaded
2. The `stm_safety` pattern was instantiated
3. The `hazard_mitigated` pattern was instantiated twice (once for each hazard)
4. Two `person` patterns were instantiated (for Alicia and Roberto)
5. The case was exported in both text and HTML formats

### Examining the Results

You can find your generated assurance case in:

- **Text Format**: `CAP/stm_system_example.txt`
- **HTML Format**: `CAP/stm_system_example/index.html` (open in a web browser)

The HTML view provides a navigable tree structure showing:
- Main safety claim for the STM system
- Hazard mitigation arguments
- Evidence status (valid, pending, or invalid)
- Personnel involved (Alicia and Roberto)

### Common Problems and Solutions

If you encounter issues, here are the most common problems and their solutions:

1. **"Pattern not found" error**:
   - **Problem**: O-ETB can't find the `stm_safety` pattern
   - **Solution**: Make sure `stm_patterns.pl` exists and is being loaded by the `load_patterns` command

2. **"Unknown procedure" error for validation**:
   - **Problem**: O-ETB can't find one of the validation predicates (e.g., `hazard_log_validate/5`)
   - **Solution**: 
     - Ensure the agent module is correctly defined with the right predicate name
     - Check that the agent is loaded in `etb.pl` with a `use_module` directive
     - Verify the spelling/naming in `categories.pl` matches your module and predicate names

3. **Evidence shows as "pending" instead of "valid"**:
   - **Problem**: Evidence files can't be found or validated
   - **Solution**:
     - Check if the evidence directories and files exist exactly as expected
     - Verify file paths in the agent code (should be `'REPOSITORY/EVIDENCE/category_name/...'`)
     - For `temp_test`, verify the file contains the word "PASS"

4. **System crashes during initialization**:
   - **Problem**: Syntax error in one of the Prolog files
   - **Solution**: Check all edited files for syntax errors, especially:
     - Missing commas between list items
     - Unmatched parentheses
     - Missing periods at the end of clauses