version 1.0

struct RuntimeAttributes {
    Int? cpu
    Float? memory
    Int? disks
    Int? preemptible
    Int? max_retries
}

workflow Classifier {
    input {
        File model_file
        Array[File] vcfs
        Array[File] vcfs_index
        String docker
        Boolean? binary_labels
        RuntimeAttributes? runtime_override
    }

    call ClassifyUsingRandomForest {
        input:
            model_file = model_file,
            vcfs = vcfs,
            vcfs_index = vcfs_index,
            docker = docker,
            binary_labels = binary_labels,
            runtime_override = runtime_override
    }

    output {
        Array[File] labeled_vcfs = ClassifyUsingRandomForest.labeled_vcfs
    }
}

task ClassifyUsingRandomForest {
    input {
        File model_file
        Array[File] vcfs
        Array[File] vcfs_index
        String docker
        Boolean? binary_labels
        RuntimeAttributes? runtime_override
    }

    output {
        Array[File] labeled_vcfs = glob("predict_*.csv")
    }

    String binary_label_flag = if select_first([binary_labels, false]) then "--binary-labels" else ""

    command {
        set -euxo pipefail

        while read VCF; do
            pzm-tools label ~{model_file} $VCF --output-prefix predict ~{binary_label_flag}
        done < ~{write_lines(vcfs)}
    }

    RuntimeAttributes runtime_default = object {
        cpu: 1,
        memory: 3.75,
        preemptible: 3,
        max_retries: 1,
        disks: 10 + (
            2 * ceil(size([
                model_file,
                vcfs], "GiB")))
    }
    RuntimeAttributes runtime_attr = select_first([runtime_override, runtime_default])

    runtime {
        docker: docker
        cpu: select_first([runtime_attr.cpu, runtime_default.cpu])
        memory: select_first([runtime_attr.memory, runtime_default.memory]) + " GiB"
        disks: "local-disk " + select_first([runtime_attr.disks, runtime_default.disks])  + " SSD"
        preemptible: select_first([runtime_attr.preemptible, runtime_default.preemptible])
        maxRetries: select_first([runtime_attr.max_retries, runtime_default.max_retries])
        noAddress: true
    }
}