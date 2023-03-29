using Cwipc;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.Controls;
using UnityEngine.XR.Interaction.Toolkit;
using UnityEngine.XR.Interaction.Toolkit.Inputs;

public class ViewAdjust : LocomotionProvider
{
    [Tooltip("The object of which the height is adjusted, and that resetting origin will modify")]
    [SerializeField] GameObject cameraOffset;

    [Tooltip("Toplevel object of this player, usually the XROrigin, for resetting origin")]
    [SerializeField] GameObject player;

    [Tooltip("Point cloud pipeline")]
    [SerializeField] PointCloudPipelineSimple pointCloudPipeline;

    [Tooltip("Camera used for determining zero position and orientation, for resetting origin")]
    [SerializeField] Camera playerCamera;

    [Tooltip("Multiplication factor for height adjustment")]
    [SerializeField] float heightFactor = 1;

    [Tooltip("The Input System Action that will be used to change view height. Must be a Value Vector2 Control of which y is used.")]
    [SerializeField] InputActionProperty m_ViewHeightAction;

    [Tooltip("Use Reset Origin action. Unset if ResetOrigin() is called from a script.")]
    [SerializeField] bool useResetOriginAction = true;

    [Tooltip("The Input System Action that will be used to reset view origin.")]
    [SerializeField] InputActionProperty m_resetOriginAction;

    // Start is called before the first frame update
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        Vector2 heightInput = m_ViewHeightAction.action?.ReadValue<Vector2>() ?? Vector2.zero;
        float deltaHeight = heightInput.y * heightFactor;
        if (deltaHeight != 0 && BeginLocomotion())
        {
            cameraOffset.transform.position += new Vector3(0, deltaHeight, 0);
            EndLocomotion();
        }
        if (useResetOriginAction && m_resetOriginAction != null)
        {
            bool doResetOrigin = m_resetOriginAction.action.ReadValue<float>() >= 0.5;
            if (doResetOrigin)
            {
                ResetOrigin();
            }
        }
    }

    void ResetOrigin()
    {
        if (BeginLocomotion())
        {
            Debug.Log("ViewAdjust: ResetOrigin");
            Vector3 pcOriginLocal = Vector3.zero; // Point cloud origin relative to pointCloudPipeline
            float pcToCameraRotationY = 0; // Rotation of camera relative to the point cloud
            if (pointCloudPipeline != null)
            {
                pcOriginLocal = pointCloudPipeline.GetPosition();
                pcToCameraRotationY =  pointCloudPipeline.transform.rotation.eulerAngles.y - playerCamera.transform.rotation.eulerAngles.y;
            }
            // Rotation of camera relative to the player
            float cameraToPlayerRotationY = playerCamera.transform.rotation.eulerAngles.y - player.transform.rotation.eulerAngles.y;
            Debug.Log($"ViewAdjust: camera rotation={cameraToPlayerRotationY}");
            // Apply the inverse rotation to cameraOffset to make the camera point in the same direction as the player
            cameraOffset.transform.Rotate(0, -cameraToPlayerRotationY, 0);
            if (pointCloudPipeline != null)
            {
                float pcToCameraNewRotationY = pointCloudPipeline.transform.rotation.eulerAngles.y - playerCamera.transform.rotation.eulerAngles.y;
                Debug.Log($"ViewAdjust: pc rotation={pcToCameraRotationY} but is {pcToCameraNewRotationY}");
                pointCloudPipeline.transform.Rotate(0, pcToCameraNewRotationY-pcToCameraRotationY, 0);
            }
            // Next set correct position on the camera
            //Vector3 moveXZ = playerCamera.transform.position - cameraOffset.transform.position;
            Vector3 moveXZ = playerCamera.transform.position - player.transform.position;
            moveXZ.y = 0;
            Debug.Log($"ResetOrigin: move cameraOffset by {moveXZ} to worldpos={playerCamera.transform.position}");
            cameraOffset.transform.position -= moveXZ;
            // Finally adjust the pointcloud position and rotate it backwards (so we don't get a double rotation)
            if (pcOriginLocal != Vector3.zero || pcToCameraRotationY != 0)
            {
                Debug.Log($"ViewAdjust: adjust pointcloud to {pcOriginLocal}");
                pointCloudPipeline.transform.localPosition = -pcOriginLocal;
               
            }
            EndLocomotion();
        }
    }

    protected void OnEnable()
    {
        m_ViewHeightAction.EnableDirectAction();
        if (useResetOriginAction) m_resetOriginAction.EnableDirectAction();
    }

    protected void OnDisable()
    {
        m_ViewHeightAction.DisableDirectAction();
        if (useResetOriginAction) m_resetOriginAction.DisableDirectAction();
    }
}
