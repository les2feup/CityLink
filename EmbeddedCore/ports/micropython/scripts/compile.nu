export def main [
    basedir: path = .
    --opt_level (-o) = 0
] {
    let basedir = $basedir | path expand
    let outbasedir = $basedir | path join ".compiled" | path expand
    let files = cd $basedir | glob **/*.py
    $files | each { |file|
        let name = $file | path basename
        let dir = $file | path dirname

        let outname = $name | str replace .py .mpy
        let extra = ($dir | str replace $basedir "") | str replace "/" ""
        let outdir = $outbasedir | path join $extra

        mkdir $outdir
        mpy-cross -O$opt_level $file -o ($outdir | path join $outname)

        {dir: $outdir, file: $outname}
    }
}
