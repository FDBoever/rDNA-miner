class Step:
    def __init__(self, name, run, inputs=None, outputs=None):

        self.name = name
        self.run = run
        self.inputs = inputs or []
        self.outputs = outputs or []

    def should_run(self, ctx):
        if ctx.force:
            return True
        for out in self.outputs:
            if not ctx.get(out).exists():
                return True
        return False

    def execute(self, ctx):
        if not self.should_run(ctx):
            ctx.logger.info(f"Skipping step: {self.name}")
            return
        ctx.logger.info(f"Running step: {self.name}")
        self.run(ctx)