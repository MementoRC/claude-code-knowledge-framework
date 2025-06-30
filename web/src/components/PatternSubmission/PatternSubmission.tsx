/**
 * Pattern Submission Component
 * Interface for contributing new patterns and reviewing submissions
 */

import React, { useState, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete,
  Alert,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  Divider,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tab,
  Tabs,
  Snackbar,
  LinearProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Preview as PreviewIcon,
  Send as SendIcon,
  Check as CheckIcon,
  Code as CodeIcon,
  Description as DescriptionIcon,
  CloudUpload as CloudUploadIcon,
} from '@mui/icons-material';

import { apiService } from '../../services/api';
import {
  PatternSubmission as PatternSubmissionType,
  PatternContributionResponse,
} from '../../types/patterns';

const PATTERN_TYPES = [
  'setup',
  'bugfix',
  'optimization',
  'best_practice',
  'architecture',
];

const COMMON_TECHNOLOGIES = [
  'React',
  'TypeScript',
  'Python',
  'FastAPI',
  'Node.js',
  'Docker',
  'PostgreSQL',
  'Redis',
  'AWS',
  'GCP',
  'JavaScript',
  'Vue.js',
  'Angular',
  'Django',
  'Flask',
  'Express.js',
  'MongoDB',
  'MySQL',
  'Kubernetes',
];

const steps = [
  'Basic Information',
  'Pattern Details',
  'Code Example',
  'Review & Submit',
];

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`submission-tabpanel-${index}`}
      aria-labelledby={`submission-tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
}

export default function PatternSubmission() {
  // Form state
  const [activeStep, setActiveStep] = useState(0);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [patternType, setPatternType] = useState('');
  const [technologies, setTechnologies] = useState<string[]>([]);
  const [codeExample, setCodeExample] = useState('');
  const [projectId, setProjectId] = useState('');
  const [additionalNotes, setAdditionalNotes] = useState('');

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [submitProgress, setSubmitProgress] = useState(0);

  // Form validation
  const isStepValid = (step: number): boolean => {
    switch (step) {
      case 0:
        return title.trim() !== '' && patternType !== '';
      case 1:
        return description.trim() !== '' && technologies.length > 0;
      case 2:
        return true; // Code example is optional
      case 3:
        return true; // Review step
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (isStepValid(activeStep)) {
      setActiveStep((prevActiveStep) => prevActiveStep + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleReset = () => {
    setActiveStep(0);
    setTitle('');
    setDescription('');
    setPatternType('');
    setTechnologies([]);
    setCodeExample('');
    setProjectId('');
    setAdditionalNotes('');
    setError(null);
    setSuccess(null);
  };

  // Submit pattern
  const handleSubmit = useCallback(async () => {
    setLoading(true);
    setError(null);
    setSubmitProgress(0);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setSubmitProgress((prev) => Math.min(prev + 10, 90));
      }, 200);

      const patternData: PatternSubmissionType = {
        document: `${title}\n\n${description}\n\n${codeExample}`,
        metadata: {
          title,
          description,
          pattern_type: patternType,
          technologies,
          code: codeExample,
          additional_notes: additionalNotes,
          submitted_at: new Date().toISOString(),
        },
        project_id: projectId || undefined,
      };

      const response: PatternContributionResponse = await apiService.contributePattern(patternData);
      
      clearInterval(progressInterval);
      setSubmitProgress(100);
      
      setSuccess(`Pattern submitted successfully! ID: ${response.pattern_id}`);
      setActiveStep(0); // Reset to first step
      
      // Clear form after successful submission
      setTimeout(() => {
        handleReset();
      }, 3000);

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Submission failed. Please try again.');
    } finally {
      setLoading(false);
      setTimeout(() => setSubmitProgress(0), 2000);
    }
  }, [title, description, patternType, technologies, codeExample, projectId, additionalNotes]);

  // Preview component
  const PatternPreview = () => (
    <Card elevation={2}>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          {title || 'Untitled Pattern'}
        </Typography>
        
        <Box sx={{ mb: 2 }}>
          <Chip label={patternType || 'No type selected'} color="secondary" />
        </Box>

        <Typography variant="body1" sx={{ mb: 2 }}>
          {description || 'No description provided'}
        </Typography>

        <Typography variant="h6" gutterBottom>
          Technologies
        </Typography>
        <Box sx={{ mb: 2 }}>
          {technologies.length > 0 ? (
            technologies.map((tech) => (
              <Chip
                key={tech}
                label={tech}
                sx={{ mr: 0.5, mb: 0.5 }}
                color="primary"
                variant="outlined"
              />
            ))
          ) : (
            <Typography variant="body2" color="text.secondary">
              No technologies specified
            </Typography>
          )}
        </Box>

        {codeExample && (
          <>
            <Typography variant="h6" gutterBottom>
              Code Example
            </Typography>
            <Paper elevation={1} sx={{ p: 2, bgcolor: 'grey.50', mb: 2 }}>
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                {codeExample}
              </pre>
            </Paper>
          </>
        )}

        {additionalNotes && (
          <>
            <Typography variant="h6" gutterBottom>
              Additional Notes
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {additionalNotes}
            </Typography>
          </>
        )}
      </CardContent>
    </Card>
  );

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Pattern Submission & Review
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Contribute new patterns to the knowledge base and help the community.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}

      {loading && submitProgress > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" gutterBottom>
            Submitting pattern...
          </Typography>
          <LinearProgress variant="determinate" value={submitProgress} />
        </Box>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper elevation={1} sx={{ p: 3 }}>
            <Stepper activeStep={activeStep} orientation="vertical">
              {/* Step 1: Basic Information */}
              <Step>
                <StepLabel>Basic Information</StepLabel>
                <StepContent>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Pattern Title"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="Enter a descriptive title for your pattern"
                        required
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth required>
                        <InputLabel>Pattern Type</InputLabel>
                        <Select
                          value={patternType}
                          onChange={(e) => setPatternType(e.target.value)}
                          label="Pattern Type"
                        >
                          {PATTERN_TYPES.map((type) => (
                            <MenuItem key={type} value={type}>
                              {type.charAt(0).toUpperCase() + type.slice(1)}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Project ID (Optional)"
                        value={projectId}
                        onChange={(e) => setProjectId(e.target.value)}
                        placeholder="Associate with a project"
                      />
                    </Grid>
                  </Grid>
                  <Box sx={{ mb: 1, mt: 2 }}>
                    <Button
                      variant="contained"
                      onClick={handleNext}
                      disabled={!isStepValid(0)}
                    >
                      Continue
                    </Button>
                  </Box>
                </StepContent>
              </Step>

              {/* Step 2: Pattern Details */}
              <Step>
                <StepLabel>Pattern Details</StepLabel>
                <StepContent>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        multiline
                        rows={4}
                        label="Description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Provide a detailed description of the pattern, when to use it, and its benefits"
                        required
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <Autocomplete
                        multiple
                        options={COMMON_TECHNOLOGIES}
                        value={technologies}
                        onChange={(_, value) => setTechnologies(value)}
                        renderInput={(params) => (
                          <TextField
                            {...params}
                            label="Technologies"
                            placeholder="Select relevant technologies"
                            required={technologies.length === 0}
                          />
                        )}
                        renderTags={(value, getTagProps) =>
                          value.map((option, index) => (
                            <Chip
                              variant="outlined"
                              label={option}
                              {...getTagProps({ index })}
                              key={option}
                            />
                          ))
                        }
                      />
                    </Grid>
                  </Grid>
                  <Box sx={{ mb: 1, mt: 2 }}>
                    <Button
                      variant="contained"
                      onClick={handleNext}
                      disabled={!isStepValid(1)}
                      sx={{ mr: 1 }}
                    >
                      Continue
                    </Button>
                    <Button onClick={handleBack}>Back</Button>
                  </Box>
                </StepContent>
              </Step>

              {/* Step 3: Code Example */}
              <Step>
                <StepLabel>Code Example</StepLabel>
                <StepContent>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        multiline
                        rows={8}
                        label="Code Example (Optional)"
                        value={codeExample}
                        onChange={(e) => setCodeExample(e.target.value)}
                        placeholder="Provide a code example demonstrating the pattern"
                        variant="outlined"
                        sx={{
                          '& .MuiInputBase-input': {
                            fontFamily: 'monospace',
                          },
                        }}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        multiline
                        rows={3}
                        label="Additional Notes (Optional)"
                        value={additionalNotes}
                        onChange={(e) => setAdditionalNotes(e.target.value)}
                        placeholder="Any additional notes, warnings, or considerations"
                      />
                    </Grid>
                  </Grid>
                  <Box sx={{ mb: 1, mt: 2 }}>
                    <Button
                      variant="contained"
                      onClick={handleNext}
                      sx={{ mr: 1 }}
                    >
                      Continue
                    </Button>
                    <Button onClick={handleBack}>Back</Button>
                  </Box>
                </StepContent>
              </Step>

              {/* Step 4: Review & Submit */}
              <Step>
                <StepLabel>Review & Submit</StepLabel>
                <StepContent>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    Please review your pattern submission before submitting.
                  </Typography>
                  
                  <PatternPreview />

                  <Box sx={{ mb: 1, mt: 2 }}>
                    <Button
                      variant="contained"
                      onClick={handleSubmit}
                      disabled={loading}
                      startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
                      sx={{ mr: 1 }}
                    >
                      {loading ? 'Submitting...' : 'Submit Pattern'}
                    </Button>
                    <Button onClick={handleBack} disabled={loading}>
                      Back
                    </Button>
                    <Button onClick={() => setPreviewOpen(true)} sx={{ ml: 1 }}>
                      <PreviewIcon sx={{ mr: 0.5 }} />
                      Preview
                    </Button>
                  </Box>
                </StepContent>
              </Step>
            </Stepper>

            {activeStep === steps.length && (
              <Paper square elevation={0} sx={{ p: 3 }}>
                <Typography>Pattern submitted successfully!</Typography>
                <Button onClick={handleReset} sx={{ mt: 1, mr: 1 }}>
                  Submit Another Pattern
                </Button>
              </Paper>
            )}
          </Paper>
        </Grid>

        {/* Sidebar with guidelines */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Submission Guidelines
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                To help maintain quality, please follow these guidelines:
              </Typography>
              <Box component="ul" sx={{ pl: 2, '& li': { mb: 1 } }}>
                <li>
                  <Typography variant="body2">
                    Provide clear, descriptive titles
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Include detailed explanations of when and how to use the pattern
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Add relevant technologies and tags
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Include working code examples when applicable
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Test your patterns before submitting
                  </Typography>
                </li>
              </Box>
            </CardContent>
          </Card>

          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Pattern Categories
              </Typography>
              {PATTERN_TYPES.map((type) => (
                <Chip
                  key={type}
                  label={type}
                  size="small"
                  sx={{ mr: 0.5, mb: 0.5 }}
                  color={patternType === type ? 'primary' : 'default'}
                  onClick={() => setPatternType(type)}
                />
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Preview Dialog */}
      <Dialog
        open={previewOpen}
        onClose={() => setPreviewOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Pattern Preview</DialogTitle>
        <DialogContent>
          <PatternPreview />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}