class ResponseParser:
    BEGIN_CALL = "----BEGIN_FUNCTION_CALL----"
    END_CALL = "----END_FUNCTION_CALL----"
    ARG_SEP = "----ARG----"
    VALUE_SEP = "----VALUE----"

    response_format = f"""your_thoughts_here
...
{BEGIN_CALL}
function_name
{ARG_SEP}
arg1_name
{VALUE_SEP}
arg1_value (can be multiline)
{ARG_SEP}
arg2_name
{VALUE_SEP}
arg2_value (can be multiline)
...
{END_CALL}

DO NOT CHANGE ANY TEST! AS THEY WILL BE USED FOR EVALUATION.
"""

    def parse(self, text: str) -> dict | None:
        """
        Parse the function call from `text` using string.rfind to avoid confusion with
        earlier delimiter-like content in the reasoning.

        Returns:
            dict with keys {"thought", "name", "arguments"} on success,
            or None if no valid function call block is found.
        """
        if text is None:
            return None

        # Find the *last* END and BEGIN markers
        end_idx = text.rfind(self.END_CALL)
        if end_idx == -1:
            return None

        begin_idx = text.rfind(self.BEGIN_CALL, 0, end_idx)
        if begin_idx == -1:
            return None

        # Everything before BEGIN is the chain-of-thought
        thought = text[:begin_idx].strip()

        # Extract body between the markers
        body_start = begin_idx + len(self.BEGIN_CALL)
        body = text[body_start:end_idx].strip()
        if not body:
            # Empty body -> no valid call
            return None

        # Split into function name + argument section
        arg_sep_idx = body.find(self.ARG_SEP)
        if arg_sep_idx == -1:
            func_name = body.strip()
            arg_section = ""
        else:
            func_name = body[:arg_sep_idx].strip()
            arg_section = body[arg_sep_idx + len(self.ARG_SEP):]

        if not func_name:
            return None

        arguments: dict[str, str] = {}
        if arg_section:
            # Each block is "arg_name\n----VALUE----\narg_value..."
            for raw_block in arg_section.split(self.ARG_SEP):
                block = raw_block.strip()
                if not block:
                    continue

                value_idx = block.find(self.VALUE_SEP)
                if value_idx == -1:
                    # Malformed arg block -> skip
                    continue

                arg_name = block[:value_idx].strip()
                arg_value = block[value_idx + len(self.VALUE_SEP):]

                # Strip a single leading newline from value (keep internal newlines)
                if arg_value.startswith("\n"):
                    arg_value = arg_value[1:]
                arg_value = arg_value.rstrip()  # optional

                if not arg_name:
                    continue
                arguments[arg_name] = arg_value

        return {"thought": thought, "name": func_name, "arguments": arguments}