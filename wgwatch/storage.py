from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class CustomManifestStaticFilesStorage(ManifestStaticFilesStorage):
    def hashed_name(self, name, content=None, filename=None):
        # Skip hashing for source.css — it's only used during Tailwind compilation
        if name == "css/source.css":
            return name
        return super().hashed_name(name, content, filename)

    def post_process(self, paths, dry_run=False, **options):
        # Exclude source.css from post-processing
        paths = {k: v for k, v in paths.items() if k != "css/source.css"}
        return super().post_process(paths, dry_run, **options)
