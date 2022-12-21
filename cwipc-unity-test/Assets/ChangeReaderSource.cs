using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ChangeReaderSource : MonoBehaviour
{
    public Cwipc.PrerecordedPointCloudReader reader;
    public string newDirectory;
    public bool change;

    // Start is called before the first frame update
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        if (change)
        {
            change = false;
            reader.dirName = newDirectory;
        }
    }
}
