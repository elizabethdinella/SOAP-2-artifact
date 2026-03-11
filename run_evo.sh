budget=120
a_budget=20
D4J_SEED=47
MAX_JOBS=48
JOBS=0

exec_cmd() {
    local cmd=$1
    local log_file=$2
    echo
    echo "Executing command:"
    echo "$cmd"
    $cmd > "$log_file" 2>&1
}

#OG=true
OG=false

for i in $(seq 1 5); do
    proj_dir=$(find SF100/ -maxdepth 1 -type d -name "${i}_*" | head -n 1)
    echo "Processing " $proj_dir
    proj_name=$(basename "$proj_dir")
    jar_path=$(echo "$proj_dir"/*.jar | tr ' ' ':')
    #jar_path=$(find "$proj_dir" -maxdepth 1 -type f -name "*.jar" | head -n 1)

    if [ -d "${proj_dir}/lib" ]; then
        lib_jars=$(echo ${proj_dir}/lib/*.jar | tr ' ' ':')
    else
        lib_jars=""
    fi
    project_cp="${jar_path}:${lib_jars}"

    for classfile in $(find "$proj_dir" -type f -name "*.class"); do
        methods=($(java -cp lib/asm-9.5.jar:lib/asm-tree-9.5.jar:src/ MethodExtractor $classfile))
        trimmed_file=$(echo "$classfile" | sed "s|^SF100/$proj_name/||; s|\.class$||")
        class=$(echo "$trimmed_file" | sed 's|/|.|g')
        echo $class

        for TARGET_METHOD in "${methods[@]}"; do
            echo "$TARGET_METHOD"

            if [ "$OG" = true ]; then
                cmd="java -cp evosuite-original-1.1.0.jar shaded.org.evosuite.EvoSuite"
                DIR_OUTPUT_PREFIX="output-original/$proj_name/$class"
            else
                cmd="java -cp muse.jar shaded.org.evosuite.EvoSuite"
                DIR_OUTPUT_PREFIX="output/$proj_name/$class"
            fi

            DIR_OUTPUT=$DIR_OUTPUT_PREFIX/$(echo "$TARGET_METHOD" | sed 's/\//_/g')/

            if [ -f "$DIR_OUTPUT/statistics.csv" ]; then
                echo "SKIP (already exists): $DIR_OUTPUT"
                continue
            fi

            # Capture loop variables for subshell
            _class="$class"
            _target="$TARGET_METHOD"
            _dir_output="$DIR_OUTPUT"
            _proj_name="$proj_name"
            _project_cp="$project_cp"
            _cmd="$cmd"

            (
                report_dir="evosuite-report-${_proj_name}-${BASHPID}"

                local_cmd="${_cmd} \
                    -class ${_class} \
                    -projectCP ${_project_cp} \
                    -seed $D4J_SEED \
                    -Dsearch_budget=$budget \
                    -Dassertion_timeout=$a_budget \
                    -Dtest_dir=${_dir_output} \
                    -Dtarget_method=${_target} \
                    -criterion branch \
                    -Dshow_progress=false \
                    -Djunit_check=false \
                    -Dfilter_assertions=false \
                    -Dtest_comments=false \
                    -mem 30000 \
                    -Dsort_calls \
                    -Dtimeline_interval=15000 \
                    -Dreport_dir=${report_dir}"

                log_file="${_dir_output}/evosuite.log"
                mkdir -p "${_dir_output}"
                if ! exec_cmd "$local_cmd" "$log_file"; then
                    echo "WARNING: failed on ${_class} ${_target}, continuing..."
                fi

                if [ -f "${report_dir}/statistics.csv" ]; then
                    mv "${report_dir}/statistics.csv" "${_dir_output}/"
                fi
                rm -rf "${report_dir}"
            ) &

            ((JOBS++))
            if [[ $JOBS -ge $MAX_JOBS ]]; then
                wait -n
                ((JOBS--))
            fi

        done
    done
done

wait
echo "All jobs complete."
